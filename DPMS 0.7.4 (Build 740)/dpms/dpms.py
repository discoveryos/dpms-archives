import argparse
from pathlib import Path

from dpms import dpms_core
from dpms import dpms_utils


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

    args = parser.parse_args()

    if args.install:
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
