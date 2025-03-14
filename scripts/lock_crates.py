"""rusted script."""

from __future__ import annotations

import tarfile
import tomllib as toml
from functools import cache as in_memory_cache
from pathlib import Path
from typing import IO, Any

import click
import yaml
from click.utils import LazyFile
from pip._internal.req import InstallRequirement
from pip._internal.req.constructors import install_req_from_req_string
from piptools.repositories import PyPIRepository
from pybuild_deps.cache import persistent_cache
from pybuild_deps.constants import PIPTOOLS_CACHE_DIR
from pybuild_deps.finder import find_build_dependencies
from pybuild_deps.logger import log
from pybuild_deps.parsers import parse_requirements
from pybuild_deps.source import get_package_source
from pybuild_deps.utils import get_version

REQUIREMENTS_TXT = "requirements.txt"
ROOT_DIR = Path(__file__).absolute().parent.parent


@click.command(context_settings={"help_option_names": ("-h", "--help")})
@click.version_option(package_name="pybuild-deps")
@click.pass_context
@click.option("-v", "--verbose", count=True, help="Show more output", default=1)
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

    repository = PyPIRepository([], cache_dir=PIPTOOLS_CACHE_DIR)
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
        cargo_deps = _get_cargo_dependencies(dep.name, dep_version)
        cargo_dependencies.extend(cargo_deps)

    # deduplicate
    _deps_as_dict = {c["filename"]: c for c in cargo_dependencies}
    cargo_dependencies = list(_deps_as_dict.values())
    log.info(f"Detected {len(cargo_dependencies)} crates.")
    # format artifact.lock.yaml structure
    artifact_lock = {"metadata": {"version": "1.0"}, "artifacts": cargo_dependencies}
    lock_contents = yaml.dump(artifact_lock, indent=2, sort_keys=False)
    output_file.write(lock_contents.encode())


@persistent_cache("lock-crates")
def _get_cargo_dependencies(dep_name: str, dep_version: str):
    raw_build_deps = find_build_dependencies(dep_name, dep_version)
    build_deps = {
        ireq.name.lower() for ireq in map(install_req_from_req_string, raw_build_deps)
    }
    has_rust_toolchain = {"maturin", "setuptools-rust"} & build_deps
    if not has_rust_toolchain:
        return []
    log.info(
        f"Found rust toolchain ({has_rust_toolchain}) for {dep_name}:{dep_version}"
    )
    deps = []
    sdist = get_package_source(dep_name, dep_version)
    log.info("searching for Cargo.lock files...")
    with tarfile.open(fileobj=sdist.open("rb")) as sdist_tarball:
        cargo_locks = [
            name
            for name in sdist_tarball.getnames()
            if name.lower().endswith("cargo.lock")
        ]
        if not cargo_locks:
            log.warning("No Cargo.lock found for {dep_name}:{dep_version}")
            return []
        if len(cargo_locks) == 1:
            lock = cargo_locks[0]
        else:
            # dirty heuristic - the lockfile closer to root dir is the winner
            # update this to brute-forcibly loop over all lockfiles if we
            # miss any dependency
            lock = sorted(cargo_locks, key=lambda x: len(x))[0]
        log.info(f"parsing crates from {lock}")
        lock_contents = sdist_tarball.extractfile(lock).read().decode()
        deps.extend(_parse_cargo_lock(lock_contents))
    return deps


def _parse_cargo_lock(lock_contents: str):
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


@in_memory_cache
def _get_base_for_crate_index(source):
    if source == "registry+https://github.com/rust-lang/crates.io-index":
        return "https://crates.io/api/v1/crates"
    # TODO: support other sources
    # https://doc.rust-lang.org/cargo/reference/registry-index.html#index-protocols
    # support for git+http can be "easily" implemented by downloading archives
    # https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives#source-code-archive-urls
    # this would, however, become unsustainable to request for EC exception for building
    # later, as each url would require an exception - and each version update would
    # require new approval... at this point it is better to avoid the problematic
    # dependency and wait for the official pip+cargo support on cachi2/hermeto
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
