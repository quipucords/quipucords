#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

from pybuild_deps.finder import find_build_dependencies
from pybuild_deps.parsers import parse_requirements
from pybuild_deps.utils import get_version

reqs = list(parse_requirements("lockfiles/requirements-build.txt")) + list(
    parse_requirements("lockfiles/requirements.txt")
)

all_build_reqs = [find_build_dependencies(r.name, get_version(r)) for r in reqs]


reqs_binaries = []
for req, build_reqs in zip(reqs, all_build_reqs):
    if req.name.lower().endswith(("maturin", "setuptools-rust")):
        continue
    joined_reqs = " ".join(build_reqs).lower()
    if joined_reqs.count("maturin") or joined_reqs.count("setuptools-rust"):
        reqs_binaries.append(req)

with Path("lockfiles/requirements-binary.txt").open("w") as f:
    for r in reqs_binaries:
        print(r.req, file=f)
