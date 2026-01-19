# ~/dpms/dpms_utils.py

import os
import getpass
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Button, Input, RadioSet, RadioButton, Static, Label
from textual import on

# Import core functions AND custom exceptions
from dpms_core import (
    make_tar, download_file, DPMSCoreError, InvalidSourceError,
    UnsupportedCompressionError, SubprocessError, NetworkError
)

# Import the new GUI entry point
from dpms_gui import main as run_gui

# Initialize rich console for standard output functions
console = Console()

# --- Authentication Helpers ---
try:
    from config import DPMS_PASSWORD_FILE
except ImportError:
    DPMS_PASSWORD_FILE = os.path.join(os.path.expanduser('~'), '.dpms', 'password')

def _get_hashed_password():
    if os.path.exists(DPMS_PASSWORD_FILE):
        with open(DPMS_PASSWORD_FILE, 'r') as f:
            return f.read().strip()
    return None

def authenticate_user():
    pass

def set_password_prompt():
    pass

# --- Textual Application for make_tar ---


class MakeTarApp(App):
    #MAke Tar APP for i dont know 
    CSS = """
    #main-container { padding: 1; }
    .input-label { width: 1fr; padding-top: 1; }
    Input { border: round #666666; height: 1fr; margin-top: 1; }
    RadioSet { border: round #666666; margin-top: 1; padding: 1; }
    .status-text { padding-top: 1; height: 3; }
    Button { width: 20; margin-top: 2; }
    """
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),("q", "quit", "Quit"),]
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield Panel("[bold green]DPMS: Interactive Archive Creation[/bold green]", subtitle="Like Linux's menuconfig, but for compression", border_style="bold green")
            yield Label("[bold]Source Path:[/bold]", classes="input-label")
            yield Input(placeholder="e.g., /path/to/my_folder", id="source-path")
            yield Label("[bold]Output Filename:[/bold]", classes="input-label")
            yield Input(placeholder="e.g., my_archive", id="output-filename")
            yield Label("[bold]Compression Type:[/bold]", classes="input-label")
            with RadioSet(id="compression-options"):
                yield RadioButton("gzip (.tar.gz)", id="gz", value=True)
                yield RadioButton("xz (.tar.xz)", id="xz")
            yield Button("Compress", variant="primary", id="compress-button")
            yield Static("", id="status-display", classes="status-text")
        yield Footer()
    def on_mount(self): self.query_one(Header).tall = True
    @on(Button.Pressed, "#compress-button")
    def on_compress_button_pressed(self):
        source_path = self.query_one("#source-path", Input).value
        output_filename = self.query_one("#output-filename", Input).value
        compression_type = self.query_one(RadioSet).pressed_button.id
        status_widget = self.query_one("#status-display", Static)
        if not source_path:
            status_widget.update(Text("Error: Source path cannot be empty.", style="bold red"))
            return
        if not output_filename:
            status_widget.update(Text("Error: Output filename cannot be empty.", style="bold red"))
            return
        status_widget.update(Text(f"Starting compression for '{source_path}'...", style="cyan"))
        self.run_worker(self.start_compression_task(source_path, output_filename, compression_type, status_widget))
    def start_compression_task(self, source_path, output_filename, compression_type, status_widget):
        try:
            make_tar(source_path, output_filename, compression_type, status_widget=status_widget)
            status_widget.update(Text("Compression finished successfully!", style="bold green"))
        except InvalidSourceError as e:
            status_widget.update(Text(f"Error: {e}", style="bold red"))
        except UnsupportedCompressionError as e:
            status_widget.update(Text(f"Error: {e}", style="bold red"))
        except SubprocessError as e:
            status_widget.update(Text(f"Subprocess Error: {e}", style="bold red"))
            if e.stderr: status_widget.update(Text(f"Stderr: {e.stderr}", style="yellow"))
        except DPMSCoreError as e:
            status_widget.update(Text(f"An error occurred in the core logic: {e}", style="bold red"))
        except Exception as e:
            status_widget.update(Text(f"An unexpected error occurred: {e}", style="bold red"))

# --- Command-line Interface ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A command-line tool for package management utilities.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    convert_parser = subparsers.add_parser('convert', help='Compress a file or folder into a tar archive.')
    convert_parser.add_argument('source_path', help='The path to the file or folder to be compressed.')
    convert_parser.add_argument('output_filename', help='The base name for the output archive file (e.g., "my_archive").')
    convert_parser.add_argument('-c', '--compression_type', choices=['gz', 'xz'], default='gz', help='The compression type to use (gz or xz). Defaults to gz.')
    download_parser = subparsers.add_parser('download', help='Download a file from a URL.')
    download_parser.add_argument('url', help='The URL of the file to download.')
    download_parser.add_argument('output_path', help='The local path to save the downloaded file.')
    interactive_parser = subparsers.add_parser('interactive', help='Start a menuconfig-style TUI for file conversion.')
    gui_parser = subparsers.add_parser('gui', help='Launch the graphical user interface.')
    help_parser = subparsers.add_parser('help', help='Show help for all commands.')
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    try:
        if args.command == 'convert':
            make_tar(args.source_path, args.output_filename, args.compression_type, verbose=args.verbose)
        elif args.command == 'download':
            download_file(args.url, args.output_path, verbose=args.verbose)
        elif args.command == 'interactive':
            app = MakeTarApp()
            app.run()
        elif args.command == 'gui':
            run_gui()
        elif args.command == 'help':
            parser.print_help()
        else:
            parser.print_help()
    except (InvalidSourceError, UnsupportedCompressionError, SubprocessError, NetworkError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if hasattr(e, 'stderr') and e.stderr: console.print(f"[yellow]Stderr:[/yellow] {e.stderr}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        sys.exit(1)
