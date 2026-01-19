# ~/dpms/dpms_utils.py

import os
import sys
import getpass
from pathlib import Path
import argparse
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

# Import core functions and exceptions
from dpms_core import (
    make_tar, download_file,
    DPMSCoreError, InvalidSourceError,
    UnsupportedCompressionError, SubprocessError, NetworkError
)

# Import GUI entry point
from dpms_gui import main as run_gui

# Initialize rich console
console = Console()

# --- Authentication Helpers ---
try:
    from config import DPMS_PASSWORD_FILE
except ImportError:
    DPMS_PASSWORD_FILE = os.path.join(os.path.expanduser('~'), '.dpms', 'password')


def _get_stored_password():
    if os.path.exists(DPMS_PASSWORD_FILE):
        with open(DPMS_PASSWORD_FILE, 'r') as f:
            return f.read().strip()
    return None


def authenticate_user():
    stored = _get_stored_password()
    if not stored:
        console.print("[yellow]No password set. Please use set_password() first.[/yellow]")
        return False
    attempt = getpass.getpass("Enter DPMS password: ")
    if attempt == stored:
        return True
    console.print("[red]Incorrect password![/red]")
    return False


def set_password():
    pw = getpass.getpass("Set a new DPMS password: ")
    confirm = getpass.getpass("Confirm password: ")
    if pw != confirm:
        console.print("[red]Passwords do not match![/red]")
        return
    os.makedirs(os.path.dirname(DPMS_PASSWORD_FILE), exist_ok=True)
    with open(DPMS_PASSWORD_FILE, 'w') as f:
        f.write(pw)
    console.print("[green]Password set successfully![/green]")


# --- CLI Utility Functions ---
def cli_compress(source_path, output_filename, compression_type='gz', verbose=False):
    try:
        make_tar(source_path, output_filename, compression_type, verbose=verbose)
        console.print(f"[green]Compression successful:[/green] {output_filename}")
    except (InvalidSourceError, UnsupportedCompressionError, SubprocessError, DPMSCoreError) as e:
        console.print(f"[red]Error:[/red] {e}")
        if hasattr(e, 'stderr') and e.stderr:
            console.print(f"[yellow]Stderr:[/yellow] {e.stderr}")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")


def cli_download(url, output_path, verbose=False):
    try:
        download_file(url, output_path, verbose=verbose)
        console.print(f"[green]Download completed:[/green] {output_path}")
    except (NetworkError, DPMSCoreError, SubprocessError) as e:
        console.print(f"[red]Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")


# --- GUI Launcher ---
def launch_gui():
    try:
        run_gui()
    except Exception as e:
        console.print(f"[red]Failed to launch GUI:[/red] {e}")


# --- Reset Configuration ---
def reset_config():
    dpms_dir = os.path.join(os.path.expanduser('~'), '.dpms')
    if os.path.exists(dpms_dir):
        try:
            import shutil
            shutil.rmtree(dpms_dir)
            console.print(f"[green]DPMS configuration reset successfully.[/green]")
        except Exception as e:
            console.print(f"[red]Failed to reset DPMS config:[/red] {e}")
    else:
        console.print("[yellow]DPMS configuration folder not found.[/yellow]")


# --- Command-Line Interface ---
def main():
    parser = argparse.ArgumentParser(description="DPMS Utilities CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Compress
    compress_parser = subparsers.add_parser("convert", help="Compress a folder into tar.gz or tar.xz")
    compress_parser.add_argument("source_path", help="Path to folder")
    compress_parser.add_argument("output_filename", help="Output archive filename")
    compress_parser.add_argument("-c", "--compression_type", choices=["gz", "xz"], default="gz")

    # Download
    download_parser = subparsers.add_parser("download", help="Download file from URL")
    download_parser.add_argument("url", help="File URL")
    download_parser.add_argument("output_path", help="Save location")

    # GUI
    subparsers.add_parser("gui", help="Launch GUI")

    # Set password
    subparsers.add_parser("set-password", help="Set DPMS password")

    # Reset config
    subparsers.add_parser("reset", help="Reset DPMS configuration")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "convert":
        cli_compress(args.source_path, args.output_filename, args.compression_type, verbose=args.verbose)
    elif args.command == "download":
        cli_download(args.url, args.output_path, verbose=args.verbose)
    elif args.command == "gui":
        launch_gui()
    elif args.command == "set-password":
        set_password()
    elif args.command == "reset":
        reset_config()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
