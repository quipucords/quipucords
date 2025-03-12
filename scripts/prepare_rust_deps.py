"""
Prepare rust dependencies.

This script generates a cargo configuration file and prepares each crate
in the specified directory as a vendored dependency.

IMPORTANT: KEEP THIS SCRIPT RELYING EXCLUSIVELY ON PYTHON STANDARD LIBRARY AS ITS
USAGE WITHIN THE BUILD PROCESS OCCUR BEFORE BUILDING ANY EXTERNAL LIBRARY.
"""

import hashlib
import json
import sys
import tarfile
from pathlib import Path
from textwrap import dedent


def _sha256(content: bytes):
    return hashlib.sha256(content).hexdigest()


def generate_cargo_checksum(crate_path: Path):
    """Generate a cargo checksum dictionary for a vendored crate.

    cargo requires a ".cargo_checksum.json" file for vendored dependencies, but
    crates downloaded from crates.io do not include this file. This function
    generates a dictionary in the expected format, which can be used to create
    the required ".cargo_checksum.json" file.
    """
    checksums = {"package": _sha256(crate_path.read_bytes()), "files": {}}
    tarball = tarfile.open(crate_path)
    for tarmember in tarball.getmembers():
        name = tarmember.name.split("/", 1)[1]  # ignore folder name
        checksums["files"][name] = _sha256(tarball.extractfile(tarmember.name).read())
    tarball.close()
    return checksums


def prepare_crate_as_vendored_dep(crate_path: Path):
    """Prepare a crate as a vendored dependency.

    Extracts the crate's contents and adds a ".cargo_checksum.json" file to make it
    compatible with Cargo's vendoring requirements.
    """
    checksums = generate_cargo_checksum(crate_path)
    with tarfile.open(crate_path) as tarball:
        folder_name = tarball.getnames()[0].split("/")[0]
        tarball.extractall(crate_path.parent, filter="data")
    cargo_checksum = crate_path.parent / folder_name / ".cargo-checksum.json"
    json.dump(checksums, cargo_checksum.open("w"))
    print(f"Wrote {cargo_checksum}")


def prepare_cargo_config(crates_path):
    """Generate a .cargo/config.toml file to configure Cargo.

    Creates a configuration file that tells cargo to search for dependencies
    in the specified crates_path instead of online repositories.
    """
    # cargo requires its config file to be located at /tmp to be recognized
    # when invoked indirectly by pip, due to pip's temporary directory changes
    config_path = Path("/tmp/.cargo/config.toml")  # noqa: S108
    config_path.parent.mkdir(exist_ok=True)
    config_content = dedent(
        f"""
            [source.crates-io]
            replace-with = "local"
            [source.local]
            directory = "{crates_path}"
        """
    )
    config_path.write_text(config_content)


def main():
    """Transform crates in proper vendored dependencies."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print("Error: missing required argument 'crates-path'")
        print("Usage: python prepare-rust-deps.py <crates-path>")
        sys.exit(2)

    crates_path = Path(sys.argv[1])

    if not crates_path.exists():
        print(f"Warning: {crates_path} not found. Assuming a connected build.")
        sys.exit()
    print(f"Preparing Rust dependencies at {crates_path}...")
    prepare_cargo_config(crates_path)
    for crate in crates_path.glob("*.crate"):
        prepare_crate_as_vendored_dep(crate)


if __name__ == "__main__":
    main()
