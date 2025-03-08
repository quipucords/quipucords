"""rusted script."""

from __future__ import annotations

import tarfile
import tomllib as toml
from functools import cache
from pathlib import Path
from typing import IO, Any

import click
import yaml
from click.utils import LazyFile
from pip._internal.req import InstallRequirement
from pip._internal.req.constructors import install_req_from_req_string
from piptools.repositories import PyPIRepository
from pybuild_deps.constants import PIP_CACHE_DIR
from pybuild_deps.finder import find_build_dependencies
from pybuild_deps.logger import log
from pybuild_deps.parsers import parse_requirements
from pybuild_deps.source import get_package_source
from pybuild_deps.utils import get_version

REQUIREMENTS_TXT = "requirements.txt"


@click.command(context_settings={"help_option_names": ("-h", "--help")})
@click.version_option(package_name="pybuild-deps")
@click.pass_context
@click.option("-v", "--verbose", count=True, help="Show more output")
@click.option("-q", "--quiet", count=True, help="Show less output")
@click.option(
    "-o",
    "--output-file",
    nargs=1,
    default="-",
    type=click.File("w+b", atomic=True, lazy=True),
    help=("Output file name. Will write to stdout by default."),
)
@click.argument(
    "src_files",
    nargs=-1,
    type=click.Path(exists=True, allow_dash=False),
)
def lock(
    ctx: click.Context,
    verbose: int,
    quiet: int,
    output_file: LazyFile | IO[Any] | None,
    src_files: tuple[str, ...],
) -> None:
    """
    Generate a lockfile of Rust transitive dependencies.

    This function analyzes the build dependencies of requirements files to detect Rust
    transitive dependencies. It relies on the presence of either maturin or
    setuptools-rust as build dependencies. If neither of these dependencies is present,
    the package is ignored.

    For setuptools-rust, this function supports newer versions that use configuration
    settings in pyproject.toml. This allows for more accurate detection of Rust
    transitive dependencies.

    The generated lockfile is in the cachi2 artifacts.lock.yml format, which is a
    generic format for locking dependencies. However, this format may change in the
    future when Rust support is fully integrated into cachi2.
    """
    log.verbosity = verbose - quiet
    if len(src_files) == 0:
        src_files = _handle_src_files()

    cargo_dependencies: list[dict] = []

    repository = PyPIRepository([], cache_dir=PIP_CACHE_DIR)
    pip_dependencies: list[InstallRequirement] = []
    for src_file in src_files:
        pip_dependencies.extend(
            parse_requirements(
                src_file,
                finder=repository.finder,
                session=repository.session,
                options=repository.options,
            )
        )

    for dep in pip_dependencies:
        dep_version = get_version(dep)
        raw_build_deps = find_build_dependencies(dep.name, dep_version)
        build_deps = {
            ireq.name.lower()
            for ireq in map(install_req_from_req_string, raw_build_deps)
        }
        has_rust_toolchain = {"maturin", "setuptools-rust"} & build_deps
        if not has_rust_toolchain:
            continue
        log.info(f"Found rust build dependencies ({has_rust_toolchain}) for {dep.req}")
        cargo_dependencies.extend(_get_cargo_dependencies(dep.name, dep_version))

    # deduplicate
    _deps_as_dict = {c["filename"]: c for c in cargo_dependencies}
    cargo_dependencies = list(_deps_as_dict.values())
    log.info(f"Collected {len(cargo_dependencies)} cargo dependencies.")
    # format artifact.lock.yaml structure
    artifact_lock = {"metadata": {"version": "1.0"}, "artifacts": cargo_dependencies}
    lock_contents = yaml.dump(artifact_lock, indent=2, sort_keys=False)
    output_file.write(lock_contents.encode())


def _get_cargo_dependencies(dep_name, dep_version):
    deps = []
    sdist = get_package_source(dep_name, dep_version)
    log.info("searching for Cargo.lock files...")
    with tarfile.open(fileobj=sdist.open("rb")) as sdist_tarball:
        cargo_locks = {
            name
            for name in sdist_tarball.getnames()
            if name.lower().endswith("cargo.lock")
        }
        # TODO: only use Cargo.lock files mapped on pyproject.toml, to filter noise
        # from packages with vendored dependencies
        for lock in cargo_locks:
            lock_contents = sdist_tarball.extractfile(lock).read().decode()
            deps.extend(_parse_cargo_lock(lock_contents))
    return deps


def _parse_cargo_lock(lock_contents: str):
    # print(lock_contents)
    deps = []
    lock = toml.loads(lock_contents)
    for package in lock["package"]:
        source = package.get("source")
        # skip "local" dependencies as we don't care about them
        # (they are presumably included as part of the package)
        if not source:
            continue
        base_url = _get_base_for_crate_index(source)
        name = package["name"]
        version = package["version"]
        checksum = package["checksum"]

        deps.append(
            {
                "download_url": f"{base_url}/{name}/{version}/download",
                "checksum": f"sha256:{checksum}",
                "filename": f"{name}-{version}.crate",
            }
        )

    return deps


@cache
def _get_base_for_crate_index(source):
    if source == "registry+https://github.com/rust-lang/crates.io-index":
        return "https://crates.io/api/v1/crates"
    # TODO: support other sources
    # https://doc.rust-lang.org/cargo/reference/registry-index.html#index-protocols
    raise NotImplementedError


def _handle_src_files():
    if Path(REQUIREMENTS_TXT).exists():
        src_files = (REQUIREMENTS_TXT,)
    else:
        raise click.BadParameter(
            f"Couldn't find a '{REQUIREMENTS_TXT}'. "
            "You must specify at least one input file."
        )

    return src_files


if __name__ == "__main__":
    lock()
