# dpms/config.py

import os


DPMS_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REPOSITORY_DIR = os.path.join(DPMS_BASE_DIR, 'packages')


INSTALL_ROOT_DIR = os.path.expanduser('~/system_root')


INSTALLED_PACKAGES_FILE = os.path.join(INSTALL_ROOT_DIR, 'installed_packages.txt')


DPMS_PASSWORD_FILE = os.path.join(DPMS_BASE_DIR, '.dpms_password')


os.makedirs(REPOSITORY_DIR, exist_ok=True)
os.makedirs(INSTALL_ROOT_DIR, exist_ok=True)
