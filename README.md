[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](/LICENSE)
[![Build Status](https://github.com/quipucords/quipucords/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/quipucords/quipucords/actions?query=branch%3Amain)
[![Test Status](https://github.com/quipucords/quipucords/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/quipucords/quipucords/actions?query=branch%3Amain)
[![Code Coverage](https://codecov.io/gh/quipucords/quipucords/branch/main/graph/badge.svg)](https://codecov.io/gh/quipucords/quipucords)


# Overview

**quipucords** is a discovery and reporting tool that scans systems across one or more networks to identify Red Hat products in an IT environment. It inspects systems using multiple methods, including direct SSH connections and APIs from platforms such as OpenShift, Red Hat Satellite, Ansible Automation Platform, and VMware vCenter.

quipucords collects and deduplicates information about operating systems, hardware, and software configurations, then generates detailed, downloadable reports. These reports help streamline routine system administration tasks related to license management, compliance tracking, and infrastructure planning.

This *README* file explains how you can run, develop, and test quipucords on your local development environment.

- [Installation](#installation)
- [Development](#development)
- [Advanced Topics](#advanced)
- [Authors](#authors)
- [Contributing](#contributing)
- [Copyright and License](#copyright)

## Usage Requirements and Assumptions

Before installing quipucords, please review the following general design principles and usage guidelines:

 * quipucords runs in Podman containers and relies on other local containers to provide supporting services such as PostgreSQL and Redis.
 * The system hosting quipucords must have direct network access to any target systems you intend to inspect.
 * For network range scans spefically:
   * Target systems must be running SSH and allow incoming connections from the quipucords host.
   * The SSH user account on the target systems should have sufficient permissions to run commands and read system files, including (optionally) allowing `sudo` privilege escalation for commands like `systemctl`.
   * The SSH user account must use the default `bash` shell. The shell *cannot* be `/sbin/nologin`, `/bin/false`, or other non-interactive programs.

## Dependencies

The Python packages that are required for running quipucords on a system can be found in the `pyproject.toml` file in the section
"tool.poetry.dependencies". Packages for development and testing are in the section "tool.poetry.group.dev.dependencies".
Finally, python packages for compiling quipucords from source can be found in `requirements-build.txt`.
# <a name="installation"></a> Installation
quipucords server is delivered as a container image on quay.io. As so, the only requirement for
it is having `podman`, `docker` or any alternative to those.

## Quick installation

```
podman run -d --name quipucords -e "QUIPUCORDS_DBMS=sqlite" -p 9443:443 -i quay.io/quipucords/quipucords:latest
```
Then open a browser and head to https://localhost:9443

## Command Line
See [qpc cli installation instructions](https://github.com/quipucords/qpc#-installation) for information.

# <a name="development"></a> Development
To work with the quipucords code, begin by cloning the repository:
```
git clone git@github.com:quipucords/quipucords.git
```

quipucords currently supports Python 3.12. Use your system package manager to ensure the correct version is available for your local environment.

## Initial setup

This project uses poetry to manage its python dependencies. To install them all, just run the following
```
poetry install
```

Quipucords environment variables for configuration. Our recommendation is to use the "poetry
dotenv" plugin to handle those (`poetry self add poetry-dotenv-plugin`), then add desired environment variables to the `.env` file. You can copy `.env.example` to get started.

### macOS build requirements

If you are building on macOS, you need to install `skopeo` and modern versions of `make`, `sed`, and `date`. The default `make`, `sed`, and `date` versions included by Apple in macOS are too old and incompatible with our build commands. If using Homebrew (`brew`), run the following:

```sh
brew install make coreutils gnu-sed skopeo
```

After installing `make`, put the updated version earlier on your `PATH` or always remember to use `gmake` instead of `make` when invoking Make targets in this project. For example:

```sh
# optionally put this in your shell rc file or add to local environment:
PATH="/usr/local/opt/make/libexec/gnubin:$PATH"
```

## Database Options
Quipucords currently supports both SQLite and PostgreSQL. The default database is an internal postgres container.

### Option 1) PostgreSQL container
All defaults point to this option. Just run the following:
```
make setup-postgres
```
### Option 2) User provided PostgreSQL instance
These are the environment variables required to configure quipucords to use a custom postgresql instance.
```
QUIPUCORDS_DBMS=postgres
QUIPUCORDS_DBMS_DATABASE=<name of the database>
QUIPUCORDS_DBMS_HOST=<hostname or ip address of the database>
QUIPUCORDS_DBMS_PASSWORD=<db password>
QUIPUCORDS_DBMS_PORT=<db port>
QUIPUCORDS_DBMS_USER=<db user>
```

### Option 3) SQLite
To use sqlite just set the following environment variable
```
QUIPUCORDS_DBMS=sqlite
```

## Redis Setup
Quipucords requires a Redis server running on port 6379 for handling background tasks and caching. There are several ways to set this up:

### Option 1) Podman
```
podman run --name redis-server -d -p 6379:6379 <your-redis-image>
```

### Option 2) Native Redis Installation
If you have Redis installed locally, ensure it's running:
```
redis-server --port 6379
```

## Initializing the Server

```
make server-init QUIPUCORDS_SERVER_PASSWORD="SuperAdmin1"
```

Both of the above commands create a superuser with name `admin` and password of `SuperAdmin1`.

## Running the Server

### Starting the API Server
To start the server with API functionality only:
```
make server-static
make serve
```
This will make the API accessible at http://127.0.0.1:8000.

To use the command line interface, you can configure access to the server by entering `qpc server config`. You can then log in by using `qpc server login`.

### Starting the Celery Worker

Open a separate terminal and run the Celery worker process:
```
make celery-worker
```
This starts a Celery worker for handling background tasks and asynchronous operations. The Celery worker must remain running alongside the server for proper operation of scheduled tasks and scans.

### Running with UI (Optional)
If you want to use the UI, you need to install [quipucords-ui](https://github.com/quipucords/quipucords-ui). Follow these steps:

1. Clone the **quipucords-ui** repository.
2. Navigate to the **quipucords-ui** directory.
3. Follow the **installation instructions** in the [quipucords-ui repository](https://github.com/quipucords/quipucords-ui).
4. Set the following environment variables according to the server configuration:
```
export QUIPUCORDS_SERVER_PROTOCOL
export QUIPUCORDS_SERVER_HOST
export QUIPUCORDS_SERVER_PORT
```
5. Start the UI with:
```
npm run start:using-server
```
This will start a proxy to communicate with the server and open the UI in your browser, typically at http://localhost:3000. The UI provides a more user-friendly way to interact with the API and manage your quipucords server.

You can log in using the **credentials provided during server setup** (e.g., **Username:** `admin`, **Password:** `SuperAdmin1` unless changed).

The full command (`npm run start:using-server`) sets up environment variables and runs parallel processes to start both the JavaScript application and open it in a browser.

### macOS Dependencies
If you intend to run on Mac OS, there are several more steps that are required.

- Increase the maxfile limit as described [here](https://github.com/ansible/ansible/issues/12259#issuecomment-173371493).
- Install sshpass as described [here](https://github.com/ansible-tw/AMA/issues/21).
- If you are running macOS 10.13 or later and you encounter unexpected crashes when running scans,
  set the environment variable `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before starting the server.
  See the explanation for this step [here](https://github.com/ansible/ansible/issues/31869#issuecomment-337769174).
- If installing dependencies fails involving openssl (`psycopg2-binary` may need this if using custom pyenv paths):
    ```
    brew install openssl
    export LDFLAGS="-I$(brew --prefix)/opt/openssl/include -L$(brew --prefix)/opt/openssl/lib"
    poetry install
    ```

## Updating the superuser's password

```
make server-set-superuser QUIPUCORDS_SERVER_PASSWORD="SuperAdmin2"
```

The above command updates the `admin` superuser password to `SuperAdmin2`.


## Linting
To lint changes that are made to the source code, run the following command:
```
make lint
```

## Testing
To run the unit tests, use the following command:
```
make test
```

To test quipucords against virtual machines running on a cloud provider, view the documentation found [here](docs/public_cloud.md).


# <a name="authors"></a> Authors
Authorship and current maintainer information can be found in [AUTHORS](AUTHORS.md).


# <a name="contributing"></a> Contributing
See the [CONTRIBUTING](CONTRIBUTING.md) guide for information about contributing to the project.


# <a name="copyright"></a> Copyright and License
Copyright 2017-2024, Red Hat, Inc.

quipucords is released under the [GNU Public License version 3](LICENSE).
