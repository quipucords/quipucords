"""
Copyright (C) 2022  Red Hat, Inc.

This software is licensed to you under the GNU General Public License,
version 3 (GPLv3). There is NO WARRANTY for this software, express or
implied, including the implied warranties of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
along with this software; if not, see
https://www.gnu.org/licenses/gpl-3.0.txt.
"""

from setuptools import find_packages, setup

setup(
    name="quipucords",
    version="0.0.0",  # just a placeholder version (cachito requires it)
    packages=find_packages(include=["quipucords"]),
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
    ],
    license="GPLv3",
    python_requires=">=3.7",
)
