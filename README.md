[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](/LICENSE)
[![Build Status](https://github.com/quipucords/quipucords/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/quipucords/quipucords/actions?query=branch%3Amain)
[![Test Status](https://github.com/quipucords/quipucords/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/quipucords/quipucords/actions?query=branch%3Amain)
[![Code Coverage](https://codecov.io/gh/quipucords/quipucords/branch/main/graph/badge.svg)](https://codecov.io/gh/quipucords/quipucords)


# Overview

**quipucords** is a discovery and reporting tool that scans systems across one or more networks to identify Red Hat products in an IT environment. It inspects systems using multiple methods, including direct SSH connections and APIs from platforms such as OpenShift, Red Hat Satellite, Ansible Automation Platform, and VMware vCenter.

quipucords collects and deduplicates information about operating systems, hardware, and software configurations, then generates detailed, downloadable reports. These reports help streamline routine system administration tasks related to license management, compliance tracking, and infrastructure planning.

This *README* file explains how you can run and test quipucords on your local development environment.

## Usage Requirements and Assumptions

Before installing quipucords, please review the following general design principles and usage guidelines:

* quipucords normally runs in Podman containers and relies on other local containers to provide supporting services such as PostgreSQL and Redis.
* The system hosting quipucords must have direct network access to any target systems you intend to inspect.
* For network range scans spefically:
  * Target systems must be running SSH and allow incoming connections from the quipucords host.
  * The SSH user account on the target systems should have sufficient permissions to run commands and read system files, including (optionally) allowing `sudo` privilege escalation for commands like `systemctl`.
  * The SSH user account must use the default `bash` shell. The shell *cannot* be `/sbin/nologin`, `/bin/false`, or other non-interactive programs.

# Prerequisites

quipucords is intended and supported only to run on Linux systems, specifically modern distributions of RHEL and Fedora. If you intend to run from source on other systems, you may encounter compatibility problems with other tools and frameworks.

Building and running quipucords locally from source requires modern versions of:

- python (>=3.12)
- uv (https://docs.astral.sh/uv/)
- podman (https://podman.io/getting-started/installation)
- skopeo
- make
- oras
- rename
- shellcheck
- yq ([the go version](https://github.com/mikefarah/yq), not the one on pypi)
- [Konflux Pipeline Patcher](https://github.com/simonbaird/konflux-pipeline-patcher)

Use your system's package manager to install or upgrade as necessary.

Note that [Konflux Pipeline Patcher](https://github.com/simonbaird/konflux-pipeline-patcher) is simply a shell script you must download like this:

```sh
# Replace $HOME/bin with wherever you keep custom scripts or programs.
mkdir -p "$HOME/bin"
curl -sL -o "$HOME/bin/pipeline-patcher" https://github.com/simonbaird/konflux-pipeline-patcher/raw/main/pipeline-patcher
chmod a+x "$HOME/bin/pipeline-patcher"

# You must include that bin dir in your PATH.
# We strongly recommend you add this to your shell's rc/profile.
export PATH="$HOME/bin:$PATH"
```

## macOS prereqs

The default versions in macOS of some programs like `make` and `sed` are too old or incompatible with our build commands. Install modern versions plus additional required programs using Homebrew:

```sh
brew install make coreutils gnu-sed skopeo oras rename yq shellcheck nmap
```

After installing some programs like `make`, update your `PATH` to override the system defaults. For example:

```sh
# We strongly recommend you add this to your shell's rc/profile.
# Some build tools do not try to use the brew prefixed program names (like `gsed` and `gdate`),
# and they WILL FAIL if you do not correctly update `PATH` to find the correct versions.
export PATH="/usr/local/opt/coreutils/libexec/gnubin:/usr/local/opt/make/libexec/gnubin:/usr/local/opt/gnu-sed/libexec/gnubin:$PATH"
```

If you are running quipucords locally on macOS to perform network scans, additionally you may need:

- Increase the maxfile limit as described [here](https://github.com/ansible/ansible/issues/12259#issuecomment-173371493).
- Install sshpass as described [here](https://github.com/ansible-tw/AMA/issues/21).
- If you are running macOS 10.13 or later and you encounter unexpected crashes when running scans,
  set the environment variable `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before starting the server.
  See the explanation for this step [here](https://github.com/ansible/ansible/issues/31869#issuecomment-337769174).

# Installation

Please note that the quipucords project alone provides *only* HTTP APIs and does not include other UIs. For a CLI, please see [`qpc`](https://github.com/quipucords/qpc/). For a browser-based GUI, please see [quipucords-ui](https://github.com/quipucords/quipucords-ui).

## Running prebuilt images

`quipucords-installer` will configure and set up all required containers *and* quipucords itself using stable, prebuilt container images, and it is the best way to quickly get started using quipucords. Using `quipucords-installer` will also install the browser-based GUI. However, `quipucords-installer` works only on systemd-based systems like RHEL and Fedora, and it provides a static installation not intended for active development purposes. See the [quipucords-installer project on GitHub](https://github.com/quipucords/quipucords-installer/) for more details.

## Running locally from source

Pull the latest quipucords code from GitHub:

```
git clone git@github.com:quipucords/quipucords.git
cd quipucords
```

### Required runtime services

Running quipucords requires a database (PostgreSQL or SQLite) and Redis. You may run PostgreSQL and Redis on your local system as "bare metal" services, but we recommend running them in containers.

#### PostgreSQL and Redis in containers

Run the following `make` targets from your cloned quipucords directory to create and start the PostgreSQL and Redis containers with known-working configurations:

```
make setup-postgres
make setup-redis
```

#### PostgreSQL and Redis elsewhere

If you choose to run PostgreSQL or Redis anywhere other than those containers, then you may need to customize environment variables for quipucords. That may include, but not be limited to, setting the following environment variables wherever quipucords will run:

```
QUIPUCORDS_DBMS=postgres
QUIPUCORDS_DBMS_DATABASE=<name of the database>
QUIPUCORDS_DBMS_HOST=<hostname or ip address of the database>
QUIPUCORDS_DBMS_PASSWORD=<db password>
QUIPUCORDS_DBMS_PORT=<db port>
QUIPUCORDS_DBMS_USER=<db user>

# Alternately, if no postgres, specify sqlite:
# QUIPUCORDS_DBMS=sqlite
```

If running on macOS with Homebrew, you may install PostgreSQL and Redis with the following commands, and you may also need to set environment variables for quipucords as described above. Further troubleshooting of these services is beyond the scope of this document.

```
brew update
brew install redis postgresql@15
brew services start redis
brew services start postgresql@15
createuser -s qpc
createdb -U qpc qpc
```

Alternatively, if you have Redis locally installed, you may try:

```
redis-server --port 6379
```

### Install Python dependencies

quipucords uses uv to manage Python dependencies. To install or update them, simply run:

```
uv sync
```

### Initialize the database

Migrate the database schema and create a user (`admin`) with the specified password:

```
read -s QUIPUCORDS_SERVER_PASSWORD
# Enter your new admin password at the prompt and press return.

make server-init QUIPUCORDS_SERVER_PASSWORD="${QUIPUCORDS_SERVER_PASSWORD}"
```

### Start the API server

To start the server with API functionality only:

```
make server-static
make serve
```

This will server the API at http://127.0.0.1:8000. However, functionality will be limited (e.g. new scans will not complete) without also running the Celery worker.

### Start the Celery worker

In a separate shell or session, start the Celery worker:

```
make celery-worker
```

This Celery worker process handles asynchronous tasks from the server. The Celery worker must remain running alongside the server to complete tasks such as performing scans, processing results, and building reports.

## Optional: qpc CLI

For a command-line client to the HTTP APIs, see [qpc cli installation instructions](https://github.com/quipucords/qpc#-installation) in the external [qpc](https://github.com/quipucords/qpc) project.

Once you have installed qpc, you can configure access to your local server with:

```
qpc server config
qpc server login
```

## Optional: quipucords-ui

Please see [quipucords-ui](https://github.com/quipucords/quipucords-ui) for more information, but a brief summary of setup steps includes:

1. Pull the latest UI code from GitHub:
    ```
    git clone git@github.com:quipucords/quipucords-ui.git
    cd quipucords-ui
    ```
2. Install dependencies via `npm install`.
3. Start the UI via `npm run start:using-server`.
4. Once started, access the UI from https://127.0.0.1:3000/.

You may also need to edit the local `.env` file or set some environment variables to match your local quipucords server. This may include:

```
export QUIPUCORDS_SERVER_PROTOCOL=http
export QUIPUCORDS_SERVER_HOST=127.0.0.1
export QUIPUCORDS_SERVER_PORT=8000
```

# Routine development tasks

## Update the admin user's password

```
read -s QUIPUCORDS_SERVER_PASSWORD
# Enter your new admin password at the prompt and press return.

make server-set-superuser QUIPUCORDS_SERVER_PASSWORD="${QUIPUCORDS_SERVER_PASSWORD}"
```

The above command updates the `admin` user's password to whatever you entered at the `read` password prompt.

## Linting

To lint all current code, run:

```
make lint
```

## Testing

To run all unit tests, run:

```
make test
```

To run only a specific test in a specific file, run:

```
uv run pytest path/to/file.py::test_function_name
```

For example:

```
uv run pytest quipucords/tests/utils/test_datetime.py::test_average_date_very_large_list_delta
```

# Contributing

See the [CONTRIBUTING](CONTRIBUTING.md) guide for information about contributing to the project.

# Copyright and License

Copyright 2017-2025, Red Hat, Inc.

quipucords is released under the [GNU Public License version 3](LICENSE).
