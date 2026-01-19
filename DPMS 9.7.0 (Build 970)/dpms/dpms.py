# ~/dpms/dpms.py
import argparse
from pathlib import Path
import subprocess
import sys

from dpms import dpms_core as core
from dpms import dpms_utils as utils

def main():
    parser = argparse.ArgumentParser(
        description="DPMS - Discovery Package Manager (cross-platform)"
    )

    parser.add_argument("--install", metavar="PKG", help="Install a package")
    parser.add_argument("--uninstall", metavar="PKG", help="Uninstall a package")
    parser.add_argument("--list", action="store_true", help="List installed packages")
    parser.add_argument("--installable", action="store_true", help="Show all installable packages")
    parser.add_argument("--reset", action="store_true", help="Reset DPMS configuration")
    parser.add_argument("--gui", action="store_true", help="Launch DPMS GUI")
    parser.add_argument("--tar", metavar="FOLDER", help="Create tar.xz from a folder")
    parser.add_argument("--get", action="store_true", help="Run DPMS-GET in the same terminal")

    args = parser.parse_args()

    if args.get:
        # Run dpms_get.py in the same terminal using the current Python executable
        subprocess.run([sys.executable, "dpms_get.py"], check=True)
    elif args.install:
        core.install_package(args.install)
    elif args.uninstall:
        core.uninstall_package(args.uninstall)
    elif args.list:
        core.list_installed()
    elif args.installable:
        core.show_installable()
    elif args.reset:
        utils.reset_config()
    elif args.gui:
        utils.launch_gui()
    elif args.tar:
        folder = Path(args.tar).expanduser().resolve()
        if folder.exists() and folder.is_dir():
            core.create_tar(folder)
        else:
            print(f"[Error] Invalid folder: {folder}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
