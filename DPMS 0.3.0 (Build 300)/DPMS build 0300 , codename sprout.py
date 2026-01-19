#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import getpass
import json
import subprocess
import platform
import tarfile
import urllib.request
import time
import requests
from pathlib import Path

try:
    import pam
except ImportError:
    pam = None

# Configuration
INSTALL_DB = Path("/var/lib/dpms/installed.json") if os.name != 'nt' else Path("installed_windows.json")
PACKAGE_DIR = Path("C:/Packages") if os.name == 'nt' else Path("/packages")
DEFAULT_GITHUB_RAW = "https://raw.githubusercontent.com/discoveryos/Dpms--pkg"
GITHUB_USER = "discoveryos"
GITHUB_REPO = "Dpms--pkg"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# Utility Functions

def init_db():
    INSTALL_DB.parent.mkdir(parents=True, exist_ok=True)
    if not INSTALL_DB.exists():
        with open(INSTALL_DB, "w") as f:
            json.dump([], f)

def load_db():
    with open(INSTALL_DB) as f:
        return json.load(f)

def save_db(data):
    with open(INSTALL_DB, "w") as f:
        json.dump(data, f, indent=2)

def check_password(username, password):
    if os.name == 'nt':
        return True
    if pam:
        p = pam.pam()
        return p.authenticate(username, password)
    else:
        print("pam module not available.")
        return False

def ask_continue(prompt):
    response = input(f"{prompt} (Y/N): ").strip().lower()
    return response == "y"

def ascii_loading_bar(task_name, duration=2):
    print(f"{task_name}: ", end="", flush=True)
    for i in range(20):
        print("=", end="", flush=True)
        time.sleep(duration/20)
    print(" done.")

# Package Functions

def download_package(pkg_name):
    for ext in ["tar.xz", "tar.gz"]:
        url = f"{DEFAULT_GITHUB_RAW}/{pkg_name}.{ext}"
        dest = PACKAGE_DIR / f"{pkg_name}.{ext}"
        try:
            print(f"Attempting download from {url}...")
            urllib.request.urlretrieve(url, dest)
            print(f"Downloaded {dest.name} successfully.")
            return dest
        except Exception as e:
            print(f"Failed to download {pkg_name}.{ext}: {e}")
    return None

def fetch_all_from_github():
    print("Fetching package list from GitHub...")
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        files = response.json()

        PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        count = 0

        for file in files:
            if file['name'].endswith(".tar.xz") or file['name'].endswith(".tar.gz"):
                url = file['download_url']
                dest = PACKAGE_DIR / file['name']
                print(f"Downloading {file['name']}...")
                urllib.request.urlretrieve(url, dest)
                count += 1

        if count == 0:
            print("No packages found in the repository.")
        else:
            print(f"Downloaded {count} packages successfully.")

    except requests.exceptions.RequestException as e:
        print(f"Error accessing GitHub API: {e}")

def install_package(pkg_name):
    pkg_name_lower = pkg_name.lower()
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    available_packages = list(PACKAGE_DIR.glob(f"{pkg_name_lower}.tar.xz")) + \
                         list(PACKAGE_DIR.glob(f"{pkg_name_lower}.tar.gz"))

    selected_package = available_packages[0] if available_packages else None

    if not selected_package:
        print(f"Package '{pkg_name}' not found locally. Downloading from GitHub...")
        selected_package = download_package(pkg_name_lower)
        if not selected_package:
            print("Download failed. Package not found.")
            return

    username = getpass.getuser()
    password = getpass.getpass(prompt=f"Password for {username}: ")
    if not check_password(username, password):
        print("Incorrect password.")
        return

    if not ask_continue("Do you want to continue installing this package?"):
        print("Installation cancelled.")
        return

    install_dir = (Path("C:/DPMS/Installed") if os.name == 'nt' else Path("/opt")) / pkg_name_lower
    install_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting to {install_dir}...")
    ascii_loading_bar("Installing")

    try:
        with tarfile.open(selected_package, "r:*") as tar:
            tar.extractall(path=install_dir)
        print(f"{pkg_name} installed successfully.")
    except Exception as e:
        print(f"Error during extraction: {e}")
        return

    installed = load_db()
    if pkg_name_lower not in [p.lower() for p in installed]:
        installed.append(pkg_name)
        save_db(installed)

def uninstall_package(pkg_name):
    pkg_name_lower = pkg_name.lower()
    username = getpass.getuser()
    password = getpass.getpass(prompt=f"Password for {username}: ")
    if not check_password(username, password):
        print("Incorrect password.")
        return

    if not ask_continue("Do you want to continue uninstalling this package?"):
        print("Uninstallation cancelled.")
        return

    install_dir = (Path("C:/DPMS/Installed") if os.name == 'nt' else Path("/opt")) / pkg_name_lower

    ascii_loading_bar("Uninstalling")

    try:
        if install_dir.exists():
            for item in install_dir.glob("*"):
                if item.is_file():
                    item.unlink()
                else:
                    import shutil
                    shutil.rmtree(item)
            install_dir.rmdir()
    except Exception as e:
        print(f"Failed to remove files: {e}")

    installed = load_db()
    installed = [p for p in installed if p.lower() != pkg_name_lower]
    save_db(installed)

    print(f"{pkg_name} uninstalled successfully.")

def show_packages():
    installed = load_db()
    if not installed:
        print("No packages installed.")
    else:
        print("Installed packages:")
        for pkg in installed:
            print(f" - {pkg}")

def show_installable():
    print("Installable packages locally:")
    local_pkgs = list(PACKAGE_DIR.glob("*.tar.xz")) + list(PACKAGE_DIR.glob("*.tar.gz"))
    if not local_pkgs:
        print("  No local packages found.")
    else:
        for p in local_pkgs:
            print(f" - {p.name}")

    print("\nAvailable on GitHub (manual check URL):")
    print(f" {DEFAULT_GITHUB_RAW}")

def launch_gui():
    current_dir = Path(__file__).parent
    gui_script = current_dir / "Dpms GUI"
    gui_script_with_ext = gui_script.with_suffix(".py")

    if gui_script.exists():
        subprocess.run(['python', str(gui_script)] if os.name == 'nt' else ['python3', str(gui_script)])
    elif gui_script_with_ext.exists():
        subprocess.run(['python', str(gui_script_with_ext)] if os.name == 'nt' else ['python3', str(gui_script_with_ext)])
    else:
        print(f"GUI script not found at: {gui_script} or {gui_script_with_ext}")

# Main Loop

def main():
    init_db()
    while True:
        try:
            cmd_input = input(": ").strip()
            if not cmd_input:
                continue

            args = cmd_input.split()
            if args[0] == '--install' and len(args) >= 2:
                install_package(args[1])
            elif args[0] == '--uninstall' and len(args) >= 2:
                uninstall_package(args[1])
            elif args[0] == '--show':
                show_packages()
            elif args[0] == '--installable':
                show_installable()
            elif args[0] == '--update-repo':
                fetch_all_from_github()
            elif args[0] == '--gui':
                launch_gui()
            elif args[0] == '--exit':
                print("Exiting DPMS.")
                break
            else:
                print("Unknown command.")
        except KeyboardInterrupt:
            print("\nUse --exit to quit.")

if __name__ == '__main__':
    if os.name != 'nt' and hasattr(os, 'geteuid') and os.geteuid() != 0:
        print("This tool must be run with sudo/root privileges.", file=sys.stderr)
        sys.exit(1)

    main()

    if os.name == 'nt':
        input("\n(Press Enter to exit...)")
