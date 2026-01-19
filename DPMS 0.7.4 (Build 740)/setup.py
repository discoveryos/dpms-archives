from setuptools import setup, find_packages

setup(
    name="dpms",
    version="0.7.4,build 740",  # bump this when we release updates
    author="Archit",  #Hey , Kevin Put the Team Name here , i dont know what its called
    description="Discovery Package Manager (DPMS) - A lightweight CLI package manager with GUI support",
    long_description=open("README.md", "r", encoding="utf-8").read() if open else "",
    long_description_content_type="text/markdown",
    url="https://github.com/discoveryos/dpms",
    packages=find_packages(),      include_package_data=True,
    install_requires=[
        "requests",
        "rich",       
        "pyqt5",      
        "tqdm"        
    ],
    entry_points={
        "console_scripts": [
            "dpms=dpms.dpms:main",  # dpms command runs main() in dpms.py
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)



#-Made on August 2025
#-Archived on 16th october 2025 
