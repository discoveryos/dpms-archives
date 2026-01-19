# setup.py
from setuptools import setup, find_packages

setup(
    name="dpms",
    version="0.9.7+build970", 
    author="Archit & Kevin (THE Discovery Team)",
    description="Discovery Package Manager (DPMS) - CLI & GUI package manager",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/discoveryos/dpms",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "rich",
        "PyQt5",
        "tqdm",
        "textual"
    ],
    entry_points={
        "console_scripts": [
            "dpms=dpms.dpms:main",  # The main terminal command
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
