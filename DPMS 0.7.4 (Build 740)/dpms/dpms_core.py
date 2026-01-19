# ~/dpms/dpms_core.py

import os
import json
import shutil
import tarfile
import zipfile
import re
import subprocess
import requests
from distutils.version import LooseVersion
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.status import Status
from rich.text import Text
from rich import print as rich_print

# Initialize a console for core logging (if called directly)
console = Console()

# Assuming config.py defines this path
try:
    from config import INSTALL_ROOT_DIR
except ImportError:
    INSTALL_ROOT_DIR = os.path.join(os.path.expanduser('~'), '.dpms', 'packages')

# --- Custom Exception Classes ---
class DPMSCoreError(Exception):
    """Base exception for errors in the dpms_core module."""
    pass

class InvalidSourceError(DPMSCoreError):
    """Raised when the source path for an operation is invalid or does not exist."""
    pass

class UnsupportedCompressionError(DPMSCoreError):
    """Raised when an unsupported compression type is specified."""
    pass

class SubprocessError(DPMSCoreError):
    """Raised when an external subprocess fails."""
    def __init__(self, message, stdout, stderr, returncode):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

class NetworkError(DPMSCoreError):
    """Raised for network-related failures (e.g., connection errors, timeouts, bad HTTP status)."""
    pass

class ArchiveError(DPMSCoreError):
    """Raised when an archive file is invalid or cannot be handled."""
    pass

# --- File Operations & Metadata Helpers ---

def _read_package_metadata_from_dir(package_dir):
    """Reads package metadata from package.json in an extracted directory."""
    meta_file = os.path.join(package_dir, 'package.json')
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            rich_print(f"[yellow]Warning: Malformed package.json in {package_dir}: {e}[/yellow]")
            return None
    return None

def _parse_package_archive_name(filename):
    """
    Parses package name and version from filenames like 'myapp-1.0.dpm'
    or 'myapp-1.0.tar.gz'.
    Returns (name, LooseVersion(version)) or (None, None) if no match.
    """
    match = re.match(r'(.+?)-(\d+(?:\.\d+)*)\.(dpm|zip|tar(?:\.gz|\.bz2|\.xz)?|tgz|tbz2|txz)$', filename, re.IGNORECASE)
    if match:
        name = match.group(1)
        version = match.group(2)
        return name, LooseVersion(version)
    return None, None

def make_tar(source_path, output_filename, compression_type='gz', status_widget=None, verbose=False):
    """
    Compresses a file or folder into a .tar.gz or .tar.xz archive.
    
    ... (This function's code is unchanged)
    """
    def log_status(message, style="white"):
        if status_widget:
            status_widget.update(Text(message, style=style))
        else:
            rich_print(message, style=style)

    if verbose:
        log_status(f"[bold cyan]Verbose mode enabled.[/bold cyan]")

    if not os.path.exists(source_path):
        raise InvalidSourceError(f"The source path '{source_path}' does not exist.")

    compression_type = compression_type.lower()
    
    if compression_type not in ['gz', 'xz']:
        raise UnsupportedCompressionError(f"Invalid compression type '{compression_type}'. Please use 'gz' or 'xz'.")
    
    if compression_type == 'gz':
        archive_filename = f"{output_filename}.tar.gz"
        try:
            if verbose:
                log_status(f"Using tarfile module for gzip compression.", style="dim")
            
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                total_files = 0
                if os.path.isfile(source_path):
                    total_files = 1
                elif os.path.isdir(source_path):
                    for _, _, files in os.walk(source_path):
                        total_files += len(files)
                
                task = progress.add_task(f"[cyan]Compressing to {archive_filename}", total=total_files)
                
                with tarfile.open(archive_filename, 'w:gz') as tar:
                    for root, _, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            tar.add(file_path, arcname=os.path.relpath(file_path, os.path.dirname(source_path)))
                            progress.update(task, advance=1)
            
            log_status(f"Successfully compressed '{source_path}' into '{archive_filename}' using gzip.", style="bold green")
        except Exception as e:
            raise DPMSCoreError(f"An error occurred during gzip compression: {e}")

    elif compression_type == 'xz':
        archive_filename = f"{output_filename}.tar.xz"
        command = ['tar', '-c', '-J', '-f', archive_filename, source_path]
        
        try:
            if verbose:
                log_status(f"Executing command: [yellow]{' '.join(command)}[/yellow]", style="dim")
            
            with Status("[bold green]Compressing using `tar` and `xz`...[/bold green]", console=console) as status:
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                if verbose:
                    log_status(f"Command stdout: {result.stdout}", style="dim")
                    log_status(f"Command stderr: {result.stderr}", style="dim")
            
            log_status(f"Successfully compressed '{source_path}' into '{archive_filename}' using xz.", style="bold green")
        except FileNotFoundError:
            raise SubprocessError("The 'tar' or 'xz' command was not found.", None, "Please ensure they are installed and in your system's PATH.", None)
        except subprocess.CalledProcessError as e:
            raise SubprocessError("An error occurred during xz compression.", e.stdout, e.stderr, e.returncode)
        except Exception as e:
            raise DPMSCoreError(f"An unexpected error occurred: {e}")

def download_file(url, output_path, verbose=False):
    """
    Downloads a file from a URL to a specified output path.
    ... (This function's code is unchanged)
    """
    if verbose:
        rich_print(f"[bold cyan]Attempting to download from:[/bold cyan] [link={url}]{url}[/link]", style="dim")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("[bold blue]{task.fields[speed]:>5.2f}MB/s"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                download_task = progress.add_task(f"[green]Downloading {os.path.basename(output_path)}", total=total_size, speed=0)
                
                for data in response.iter_content(chunk_size=4096):
                    f.write(data)
                    progress.update(download_task, advance=len(data), speed=progress.tasks[0].speed)
        
        rich_print(f"[bold green]Successfully downloaded[/bold green] to '{output_path}'.")
        
    except requests.exceptions.HTTPError as e:
        raise NetworkError(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
    except requests.exceptions.ConnectionError:
        raise NetworkError("Connection Error: A connection could not be established. Check your internet connection or URL.")
    except requests.exceptions.Timeout:
        raise NetworkError("Timeout Error: The request timed out.")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"An unexpected network error occurred: {e}")
    except Exception as e:
        raise DPMSCoreError(f"An error occurred during file download: {e}")

def extract_archive(archive_path, destination_dir, verbose=False):
    """
    Extracts a compressed archive to a destination directory.
    
    Args:
        archive_path (str): The path to the archive file.
        destination_dir (str): The directory to extract the contents to.
        verbose (bool): If True, prints extra information.
    
    Raises:
        InvalidSourceError: If the archive path does not exist.
        ArchiveError: If the archive format is unsupported or invalid.
    """
    if not os.path.exists(archive_path):
        raise InvalidSourceError(f"The archive '{archive_path}' does not exist.")
    
    os.makedirs(destination_dir, exist_ok=True)
    
    try:
        if tarfile.is_tarfile(archive_path):
            if verbose:
                rich_print(f"[bold cyan]Extracting tar archive:[/bold cyan] {archive_path}", style="dim")
            with tarfile.open(archive_path) as tar:
                tar.extractall(path=destination_dir)
        elif zipfile.is_zipfile(archive_path):
            if verbose:
                rich_print(f"[bold cyan]Extracting zip archive:[/bold cyan] {archive_path}", style="dim")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(destination_dir)
        else:
            raise ArchiveError(f"Unsupported archive format for '{archive_path}'. Only .tar.gz, .tar.xz, and .zip are supported.")
        
        rich_print(f"[bold green]Successfully extracted[/bold green] to '{destination_dir}'.")
        
    except (tarfile.TarError, zipfile.BadZipFile, IOError) as e:
        raise ArchiveError(f"Failed to extract archive: {e}")
    except Exception as e:
        raise DPMSCoreError(f"An unexpected error occurred during extraction: {e}")

def install_package(package_url, verbose=False):
    """
    Installs a package by downloading and extracting it to the installation root.
    
    Args:
        package_url (str): The URL of the package archive.
        verbose (bool): If True, enables verbose output for all steps.
    
    Raises:
        All exceptions from `download_file` and `extract_archive`.
    """
    # 1. Determine a temporary file name and the final package name
    archive_filename = package_url.split('/')[-1]
    temp_path = os.path.join(os.path.expanduser('~'), 'dpms_temp', archive_filename)
    
    # 2. Download the package
    rich_print(f"[bold blue]Step 1/2:[/bold blue] Downloading package from [link={package_url}]{package_url}[/link]...")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    download_file(package_url, temp_path, verbose=verbose)
    
    # 3. Extract the package
    rich_print(f"[bold blue]Step 2/2:[/bold blue] Extracting package...")
    
    package_name, _ = _parse_package_archive_name(archive_filename)
    if not package_name:
        raise ArchiveError("Could not determine package name from archive filename.")
        
    package_install_dir = os.path.join(INSTALL_ROOT_DIR, package_name)
    extract_archive(temp_path, package_install_dir, verbose=verbose)

    # Clean up the temporary archive file
    os.remove(temp_path)
    if verbose:
        rich_print(f"[dim]Removed temporary file:[/dim] {temp_path}", style="dim")
        
    rich_print(f"[bold green]Installation complete![/bold green] Package '{package_name}' installed to '{package_install_dir}'.")
