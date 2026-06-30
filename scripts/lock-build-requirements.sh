#!/bin/bash
# Lock Python build dependencies into lockfiles/requirements-build.txt.
#
# pybuild-deps discovers build-time deps by probing each package — for packages
# without a pre-built wheel it attempts a source build to find what's needed.
# On Linux this runs natively. On other platforms (macOS) it automatically spins
# up a Linux container using the host's native CPU architecture.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_IMAGE="registry.access.redhat.com/ubi10/ubi-minimal"
PYBUILD_DEPS_SPEC="pybuild-deps>=0.5.0,<1.0.0"

compile_natively() {
    cd "$PROJECT_ROOT"
    uv run pybuild-deps compile lockfiles/requirements.txt \
        -o lockfiles/requirements-build.txt
}

find_container_runtime() {
    local runtime
    for runtime in podman docker; do
        if command -v "$runtime" &>/dev/null; then
            echo "$runtime"
            return
        fi
    done
    echo "error: podman or docker is required to lock build requirements on $(uname -s)/$(uname -m)" >&2
    exit 1
}

native_platform() {
    case "$(uname -m)" in
        arm64|aarch64) echo "linux/arm64" ;;
        x86_64)        echo "linux/amd64" ;;
        *)             echo "linux/$(uname -m)" ;;
    esac
}

compile_in_container() {
    local runtime platform
    runtime="$(find_container_runtime)"
    platform="$(native_platform)"
    echo "Running pybuild-deps in a $platform container via $runtime..."
    "$runtime" run --rm \
        --platform "$platform" \
        -v "$PROJECT_ROOT:/work" \
        -w /work \
        "$PYTHON_IMAGE" \
        bash -c "
            microdnf install -y python3.12 python3.12-pip git &&
            python3.12 -m pip install -q '$PYBUILD_DEPS_SPEC' &&
            python3.12 -m pybuild_deps compile lockfiles/requirements.txt \
                -o lockfiles/requirements-build.txt
        "
}

if [[ "$(uname -s)" == "Linux" ]]; then
    compile_natively
else
    compile_in_container
fi
