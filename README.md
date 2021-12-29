[![GitHub license](https://img.shields.io/github/license/quipucords/quipucords.svg)](https://github.com/quipucords/quipucords/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/quipucords/quipucords.svg?branch=master)](https://travis-ci.org/quipucords/quipucords)
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

quipucords currently supports Python 3.6. If you do not have Python on your system, follow these [instructions](https://www.python.org/downloads/).


## Setting Up a Virtual Environment
Developing inside a virtual environment is recommended. Add desired environment variables to the `.env` file before creating your virtual environment.  You can copy `.env.example` to get started.

On Mac run the following command to set up a virtual environment:
```
brew install pipenv
pipenv shell
pip install -r dev-requirements.txt
```

On Linux run the following command to set up a virtual environment:
```
sudo yum install python-tools
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
To initialize the server with Postgres, run the following command:
```
make server-init
```

Both of the above commands create a superuser with name `admin` and password of `qpcpassw0rd`.

## Running the Server
To run the development server using Postgres, run the following command:
```
make serve
```
To log in to the server, you must connect to http://127.0.0.1:8000/admin/ and provide the superuser credentials.

After logging in, you can change the password and also go to some of the browsable APIs such as http://127.0.0.1:8000/api/v1/credentials/.
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

## Container Image
The quipucords container image can be created from source. This quipucords repository includes a Dockerfile that contains instructions for the image creation of the server.
You must have [Docker installed](https://docs.docker.com/engine/installation/) to create the image and run the container.  The following examples all use version `0.0.46` but any version could be used.

1. Clone the repository:
    ```
    git clone git@github.com:quipucords/quipucords.git
    git clone git@github.com:quipucords/quipucords-ui.git
    ```

2. *Optional* - Build UI:
    ```
    brew install yarn (if you don't already have yarn)
    make build-ui
    ```

    _NOTE:_ You will need to install NodeJS.  See `<https://nodejs.org/>`_.

3. Build the Docker image:
    ```
    docker -D build . -t quipucords:0.0.46
    ```
      _NOTE:_ The need to use ``sudo`` for this step is dependent upon on your system configuration.

4. There are many different options for running the QPC server.

   A. Run the Docker image with Postgres container:
    ```
    docker run --name qpc-db -e POSTGRES_PASSWORD=password -d postgres:14.1
    export QPC_VAR_DATA=$PWD/var/data
    mkdir -p $QPC_VAR_DATA
    docker run --name quipucords --link qpc-db:qpc-link -d -e QPC_DBMS_HOST=qpc-db -p 9443:443 -v $QPC_VAR_DATA:/var/data -i quipucords:0.0.46
    ```

   B. Run the Docker image with external Postgres container:
    ```
    ifconfig (get your computer's external IP if Postgres is local)
    docker run -d --name quipucords -e "QPC_DBMS_PASSWORD=password" -e"QPC_DBMS_HOST=EXTERNAL_IP" -p 9443:443 -i quipucords:0.0.46
    ```

   C. Run the Docker image with SQLite:
    ```
    docker run -d --name quipucords -e "QPC_DBMS=sqlite" -p 9443:443 -i quipucords:0.0.46
    ```

   D. For debugging purposes you may want to run the Docker image with the `/app` directory mapped to your local clone of quipucords and the logs mapped to a temporary directory. Mapping the `/app` directory allows you to rapidly change server code without having to rebuild the container. Mapping the logs to `/tmp` allows you to tail a local copy without having to exec into the container.
    ```
    docker run -d --name quipucords -e "QPC_DBMS=sqlite" -p 9443:443 -v /path/to/local/quipucords/:/app -v /tmp:/var/log -i quipucords:0.0.46
    ```

5. Configure the CLI by using the following commands:
    ```
    qpc server config --host 127.0.0.1
    qpc server login
    ```
6.  You can work with the APIs, the CLI, and UI (visit https://127.0.0.1:9443 if you installed the UI in step 2 above).

7. To enter the container use the following command:
    ```
    docker exec -it quipucords bash
    ```

8. If you need to restart the server inside of the container, run the following after entering the container to get the server PIDs and restart:
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

