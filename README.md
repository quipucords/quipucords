[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](/LICENSE)
[![Build Status](https://github.com/quipucords/quipucords/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/quipucords/quipucords/actions?query=branch%3Amaster)
[![Test Status](https://github.com/quipucords/quipucords/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/quipucords/quipucords/actions?query=branch%3Amaster)
[![Code Coverage](https://codecov.io/gh/quipucords/quipucords/branch/master/graph/badge.svg)](https://codecov.io/gh/quipucords/quipucords)
[![Documentation Status](https://readthedocs.org/projects/quipucords/badge/)](https://quipucords.readthedocs.io/en/latest/)
[![Updates](https://pyup.io/repos/github/quipucords/quipucords/shield.svg)](https://pyup.io/repos/github/quipucords/quipucords/)
[![Python 3](https://pyup.io/repos/github/quipucords/quipucords/python-3-shield.svg)](https://pyup.io/repos/github/quipucords/quipucords/)


# Overview
quipucords - Tool for discovery, inspection, collection, deduplication, and reporting on an IT environment.  quipucords is a *Python* based information gathering tool. quipucords provides a server base infrastructure for process tasks that discover and inspect remote systems by utilizing *Ansible* while additionally looking to integrate and extract data from systems management solutions. quipucords collects basic information about the operating system, hardware, and application data for each system. quipucords is intended to help simplify some of the basic system administrator tasks that are a part of the larger goal of managing licensing renewals and new deployments.

This *README* file contains information about the installation and development of quipucords, as well as instructions about where to find basic usage, known issue, and best practices information.

- [Installation](#installation)
- [Development](#development)
- [Advanced Topics](#advanced)
- [Issues](#issues)
- [Authors](#authors)
- [Contributing](#contributing)
- [Copyright and License](#copyright)

## Requirements and Assumptions
Before installing quipucords on a system, review the following guidelines about installing and running quipucords:

 * quipucords is written to run on RHEL or Centos servers.
 * The system that quipucords is installed on must have access to the systems to be discovered and inspected.
 * The target systems must be running SSH.
 * The user account that quipucords uses for the SSH connection into the target systems must have adequate permissions to run commands and read certain files, such as privilege escalation required for the ``systemctl`` command.
 * The user account that quipucords uses for a machine requires an sh shell or a similar shell. For example, the shell *cannot* be a /sbin/nologin or /bin/false shell.

The Python packages that are required for running quipucords on a system can be found in the `dev-requirements.txt` file. The Python packages that are required to build and test quipucords from source can be found in the `requirements.txt` and `dev-requirements.txt` files.

# <a name="installation"></a> Installation
quipucords is delivered with an RPM command line tool and a server container image. The following information contains instructions for installing each of these items.

## Command Line
See [qpc cli installation instructions](https://github.com/quipucords/qpc#-installation) for information.

# <a name="development"></a> Development
To work with the quipucords code, begin by cloning the repository:
```
git clone git@github.com:quipucords/quipucords.git
```

quipucords currently supports Python 3.9. If you do not have Python on your system, follow these [instructions](https://www.python.org/downloads/).

## Setting Up a Tool to Manage Multiple Runtime Versions
*asdf* is a single CLI tool and command interface that manages each of the project runtimes. It isn't mandatory, but highly recommended. You could alternatively install *pyenv* and *nvm*. For the instructions below we will assume you have it installed.

See [asdf installation instructions](http://asdf-vm.com/guide/getting-started.html#_1-install-dependencies) for more information.
```
asdf plugin-add python
asdf plugin-add nodejs
```
In order to properly install *python* versions, you will also need to install [additional dependencies](https://github.com/pyenv/pyenv/wiki#suggested-build-environment) .

For the proper installation of *node* versions, you will need to include the *g++* package. The name of the package will vary according to your OS of choice. 

On Fedora:
```
dnf install gcc-g++
```
On Rhel8:
```
dnf group install "Development Tools"
```
Install versions needed:
```
asdf install python latest:3.9
asdf install python 2.7.18
asdf install nodejs 14.18.3
```

## Setting Up a Virtual Environment
Developing inside a virtual environment is recommended. Add desired environment variables to the `.env` file before creating your virtual environment.  You can copy `.env.example` to get started.

On Mac run the following command to set up a virtual environment:
```
asdf local python latest:3.9
pip install -U pip
brew install pipenv
pipenv shell
pip install -r dev-requirements.txt
```

On Linux run the following command to set up a virtual environment:
```
asdf local python latest:3.9
pip install -U pip
pip3 install pipenv
pipenv shell
pip install -r dev-requirements.txt
```

## Database Options
Quipucords currently supports development in both SQLite and Postgres. The default database is an internal postgres container.

Using a Postgres container:
```
make setup-postgres
docker ps
```

Using a SQLite DB:
```
export QPC_DBMS=SQLite
```

## Initializing the Server
To initialize the server with SQlite, run the following command:
```
make server-init -e QPC_DBMS=sqlite
```
To initialize the server with Postgres, run the following command:
```
make server-init
```

Both of the above commands create a superuser with name `admin` and password of `qpcpassw0rd`.

## Running the Server
Currently, quipucords needs quipucords-ui to run. Both projects need to be on the same root
folder, like shown below:

/quipucords  
   --quipucords  
   --quipucords-ui

See [quipucords-ui installation instructions](https://github.com/quipucords/quipucords-ui) for further information.

To run the development server using SQlite, run the following command:
```
make build-ui
make serve -e QPC_DBMS=sqlite
```
To run the development server using Postgres, run the following command:
```
make build-ui
make serve
```
To log in to the server, you must connect to http://127.0.0.1:8000/admin/ and provide the superuser credentials stated above.

After logging in, you can change the password and also go to some browsable APIs such as http://127.0.0.1:8000/api/v1/credentials/.
To use the command line interface, you can configure access to the server by entering `qpc server config`. You can then log in by using `qpc server login`.

### macOS Dependencies
If you intend to run on Mac OS, there are several more steps that are required.

- Increase the maxfile limit as described [here](https://github.com/ansible/ansible/issues/12259#issuecomment-173371493).
- Install sshpass as described [here](https://github.com/ansible-tw/AMA/issues/21).
- Install coreutils to obtain the gtimeout command. To do this step, run the `brew install coreutils` command.
- If you are running macOS 10.13 or later and you encounter unexpected crashes when running scans,
  set the environment variable `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before starting the server.
  See the explanation for this step [here](https://github.com/ansible/ansible/issues/31869#issuecomment-337769174).
- Install gtimeout using `brew install coreutils`
- If installing dependencies fails involving openssl:
    ```
    brew install openssl
    pip uninstall pycurl
    PYCURL_SSL_LIBRARY=openssl pip --no-cache-dir install --install-option="--with-openssl" --install-option="--openssl-dir=$(brew --prefix)/opt/openssl" pycurl

    export LDFLAGS=-L/usr/local/opt/openssl/lib
    export CPPFLAGS=-I/usr/local/opt/openssl/include
    export PYCURL_SSL_LIBRARY=openssl
    ```

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

To test quipucords against virtual machines running on a cloud provider, view the documentation found [here](https://github.com/quipucords/quipucords/blob/master/docs/public_cloud.md).

# <a name="advanced"></a> Advanced Topics

##  Installing and running the server and database containers 
The quipucords container image can be created from source. This quipucords repository includes a Dockerfile that contains instructions for the image creation of the server.
You must have [Docker installed](https://docs.docker.com/engine/installation/) or [Podman installed](https://podman.io/getting-started/installation).
The examples below all use `podman` but can be replaced with `docker` unless stated otherwise.
1. Clone the repository:
   ```
   git clone git@github.com:quipucords/quipucords.git
   ```

2. Build the container image:  
   ```
   podman build -t quipucords .
   ```
3. Run the container:  
   The container can be run with either of the following methods:  

      A. Run with podman pod (podman exclusive):
         Register server to register.redhat.io:
      ```
         sudo su -
         subscription-manager register
         dnf install -y podman
         podman login registry.redhat.io
         #Make directories
         mkdir -p /var/discovery/server/volumes/data
         mkdir -p /var/discovery/server/volumes/log
         mkdir -p /var/discovery/server/volumes/sshkeys
     ```
    At the prompt, enter your username for the Red Hat Container Catalog, also known as the registry.redhat.io image registry website.

    Run the quipucords server container:
     ```
         podman run --name qpc-db \
                    --pod new:quipucords-pod \
                    --publish 9443:443 \
                    --restart on-failure \
                    -e POSTGRESQL_USER=qpc \
                    -e POSTGRESQL_PASSWORD=qpc \
                    -e POSTGRESQL_DATABASE=qpc-db \
                    -v qpc-data:/var/lib/pgsql/data \
                    -d postgres:14.1
    ```
    Run the quipucords database container:
    ```
         podman run \
                --name discovery \
                --restart on-failure \
                --pod quipucords-pod \
                -e DJANGO_DEBUG=False \
                -e NETWORK_CONNECT_JOB_TIMEOUT=600 \
                -e NETWORK_INSPECT_JOB_TIMEOUT=10800 \
                -e PRODUCTION=True \
                -e QPC_DBMS_HOST=qpc-db \
                -e QPC_DBMS_PASSWORD=qpc \
                -e QPC_DBMS_USER=qpc \
                -e QPC_SERVER_TIMEOUT=5 \
                -e QPC_SERVER_USERNAME=admin \
                -e QPC_SERVER_PASSWORD=q1w2e3r4 \
                -e QPC_SERVER_USER_EMAIL=admin@example.com \
                -v /var/discovery/server/volumes/data/:/var/data:z \
                -v /var/discovery/server/volumes/log/:/var/log:z \
                -v /var/discovery/server/volumes/sshkeys/:/sshkeys:z \
                -d quipucords
   ```
   
     B. Run with external Postgres container:

   ```
   ifconfig (get your computer's external IP if Postgres is local)
   podman run -d --name quipucords -e "QPC_DBMS_PASSWORD=password" 
   -e"QPC_DBMS_HOST=<ip_address_from_ifconfig>" -p 9443:443 -i quipucords
   ```
     C. Run with SQlite 
   
   ```
   podman run -d --name quipucords -e "QPC_DBMS=sqlite" -p 9443:443 -i quipucords
   ```
     D. For debugging purposes you may want to run the Docker image with the /app directory mapped to your local clone of quipucords and the logs mapped to a temporary directory. Mapping the /app directory allows you to rapidly change server code without having to rebuild the container. 
   ```
   podman run -d --name quipucords -e "QPC_DBMS=sqlite" -p 9443:443 -v 
   /path/to/local/quipucords/:/app -v /tmp:/var/log -i quipucords
   ```
##  Installing and running the server and database with Docker Compose

1. Clone the repository:
   ```
   git clone git@github.com:quipucords/quipucords.git
   ```

2. Build UI:  
Currently, quipucords needs quipucords-ui to run while using Docker Compose installation method.  
Both projects need to be on the same root folder, like shown below:
/quipucords  
   --quipucords  
   --quipucords-ui

   
   See [quipucords-ui installation instructions](https://github.com/quipucords/quipucords-ui) for further information.  
   You will need to have NodeJS installed. See [Nodejs](<https://nodejs.org/>) official website for instructions.  
   
   On Mac:
   ```
   brew install yarn (if you don't already have yarn)
   make build-ui 
   ```
 
   On Linux:
   
```
   npm install yarn (if you don't already have yarn)
   make build-ui 
 ```
3. Build the Docker image through Docker-compose:

   For Linux users using Podman instead of Docker, this one-time setup is necessary:
   ```
   systemctl enable --user podman.socket
   systemctl start --user podman.socket
   # add the next line to your ~/.bashrc (or equivalent)
   export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
   ```
   then run:
   ```
   docker-compose up -d
   ```
   _NOTE:_ The need to use ``sudo`` for this step is dependent upon on your system configuration.  

   For Mac users:
   ```
   docker-compose up -d

##  Further steps and configuration
1. Configure the CLI by using the following commands:
    ```
    qpc server config --host 127.0.0.1
    qpc server login
    ```
2. You can work with the APIs, the CLI, and UI (visit https://127.0.0.1:9443 if you installed the UI in one of the steps above).

3. To enter the container use the following command:
    ```
    docker exec -it quipucords bash
    ```

4. If you need to restart the server inside of the container, run the following after entering the container to get the server PIDs and restart:
    ```
    ps -ef | grep gunicorn
    kill -9 PID PID
    ```
    _NOTE:_ There are usually multiple gunicorn processes running. You can kill them all at once by listing PIDs as shown in the example above.

## Running quipucords server in gunicorn
You can run the server locally inside of gunicorn.  This can be a useful way to debug.

1. Clone the repository:
    ```
    git clone git@github.com:quipucords/quipucords.git
    cd quipucords
    ```
2. Switch to quipucords django app module:
    ```
    cd quipucords
    ```

3. Make symbolic link to ansible roles:
    ```
    ln -s ../roles/ roles
    ```
4. Start gunicorn:
    ```
    gunicorn quipucords.wsgi -c ./local_gunicorn.conf.py
    ```
5. Configure the CLI by using the following commands:
    ```
    qpc server config --host 127.0.0.1 --port 8000
    qpc server login
    ```
# <a name="issues"></a> Issues
To report bugs for quipucords [open issues](https://github.com/quipucords/quipucords/issues) against this repository in Github. Complete the issue template when opening a new bug to improve investigation and resolution time.


# <a name="authors"></a> Authors
Authorship and current maintainer information can be found in [AUTHORS](AUTHORS.md).


# <a name="contributing"></a> Contributing
See the [CONTRIBUTING](CONTRIBUTING.md) guide for information about contributing to the project.


# <a name="copyright"></a> Copyright and License
Copyright 2017-2019, Red Hat, Inc.

quipucords is released under the [GNU Public License version 3](LICENSE).

