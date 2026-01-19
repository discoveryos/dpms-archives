# ~/dpms/dpms_get.py

import sys
import argparse
from rich.console import Console
from dpms_core import (
    install_package, remove_package, search_package,
    DPMSCoreError, NetworkError, ArchiveError, InvalidSourceError
)
from dpms_tags import show_version, show_package_info
from dpms_utils import main as dpms_utils_main  # To go back to DPMS

console = Console()
DPMS_GET_VERSION = "0.9.3-alpha"

def main():
    console.print("[bold green]Welcome to DPMS - GET[/bold green]")
    console.print("To go back to DPMS, type [bold yellow]--exit[/bold yellow]\n")

    parser = argparse.ArgumentParser(
        description="DPMS GET - package management interface"
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-V", "--version", action="store_true", help="Show DPMS GET version")
    parser.add_argument("--exit", action="store_true", help="Return to DPMS main terminal")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a package")
    install_parser.add_argument("package_identifier", help="Package name or URL")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove installed package")
    remove_parser.add_argument("package_name", help="Package name")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for a package")
    search_parser.add_argument("query", help="Search term")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show package information")
    info_parser.add_argument("package_name", help="Package name")

    # Parse known args first for --exit or --version
    args, unknown = parser.parse_known_args()

    if args.version:
        show_version("DPMS-GET")
        sys.exit(0)

    if args.exit:
        console.print("[cyan]Returning to DPMS main terminal...[/cyan]\n")
        dpms_utils_main()  # Opens DPMS in same terminal
        return

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    # Parse args properly
    args = parser.parse_args()

    try:
        if args.command == "install":
            install_package(args.package_identifier, verbose=args.verbose)
        elif args.command == "remove":
            remove_package(args.package_name, verbose=args.verbose)
        elif args.command == "search":
            search_package(args.query, verbose=args.verbose)
        elif args.command == "info":
            show_package_info(args.package_name, verbose=args.verbose)
        else:
            parser.print_help()

    except (DPMSCoreError, NetworkError, ArchiveError, InvalidSourceError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    main()
