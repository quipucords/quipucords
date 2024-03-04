#!/usr/bin/env python
"""quipucords setup."""

from setuptools import find_packages, setup

setup(
    name="quipucords",
    version="0.0.0",  # just a placeholder version (cachito requires it)
    packages=find_packages(include=["quipucords"]),
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.11",
    ],
    license="GPLv3",
    python_requires=">=3.11",
)
