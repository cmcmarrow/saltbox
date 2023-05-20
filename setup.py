# built-in
import setuptools
from distutils.core import setup
import os


setup(
    name="saltbox",
    version=f"0.1.0",
    author="Charles McMarrow",
    license="Apache Software License 2.0",
    description="A playground for salt",
    packages=["saltbox",
              "saltbox.boxs",
              "saltbox.builders",
              "saltbox.utils"],

    install_requires=["pyyaml", "docker"],

    classifiers=["Development Status :: 2 - Pre-Alpha",
                 "Environment :: Console",
                 "Intended Audience :: Developers",
                 "Natural Language :: English",
                 "Operating System :: POSIX :: Linux",
                 "Operating System :: MacOS :: MacOS X",
                 "Programming Language :: Python :: 3.8",
                 "Programming Language :: Python :: 3.9",
                 "Programming Language :: Python :: 3.10"],

    entry_points={"console_scripts": ["saltbox = saltbox.saltidle:run"]}
)
