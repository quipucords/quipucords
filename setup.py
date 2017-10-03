#!/usr/bin/env python
# coding=utf-8
"""A setuptools-based script for installing quipucords."""
import os
import sys
from setuptools import setup, find_packages

BASE_QPC_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]), '.')))
sys.path.insert(0, os.path.join(BASE_QPC_DIR, 'quipucords'))
# pylint: disable=wrong-import-position
from qpc import __version__  # noqa: E402

setup(
    name='quipucords',
    version=__version__,
    author='Quipucords Team',
    author_email='quipucords@redhat.com',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    include_package_data=True,
    license='GPLv3',
    packages=find_packages(exclude=['test*.py']),
    package_data={'': ['LICENSE']},
    url='https://github.com/quipucords/quipucords',
    scripts=[
        'bin/qpc',
    ],
    zip_safe=False
)
