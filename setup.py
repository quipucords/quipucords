#!/usr/bin/env python
# coding=utf-8
"""A setuptools-based script for installing quipucords."""
from setuptools import setup

setup(
    name='quipucords',
    author='Quipucords Team',
    author_email='quipucords@redhat.com',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    include_package_data=True,
    license='GPLv3',
    package_data={'': ['LICENSE']},
    url='https://github.com/quipucords/quipucords',
)
