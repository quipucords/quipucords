# Installation

This document describes two methods of building and running quipucords containers locally from source for testing and development:

1. install and run containers in a podman pod
2. install and run containers via podman compose

These methods are not officially supported for downstream users. Downstream users should always refer to official Red Hat documentation for running the Red Hat-managed downstream container images.

## Podman Setup

See also [Podman installation docs](https://podman.io/getting-started/installation).

* If running on Fedora/Centos/RHEL,
   ```
   sudo subscription-manager register
   sudo dnf install -y podman
   ```
* If running on macOS,
   ```
   brew install podman
   podman machine init --volume "${HOME}"
   podman machine start
   ```
   The `--volume` argument here is required because by default `podman` on macOS does not permit mounting any host directories into guest containers. You must specify individual directories or a common parent directory when first initializing the machine. You may adjust this value as needed. If you intend to store quipucords source code ourside of your home directory tree, you must update the value accordingly. If you already have a podman machine, you should `podman machine rm` it or define and start a _new_ machine with the appropriate volume argument.

## Option 1: Install and run containers in a podman pod

This method builds and runs quipucords container image from your local source alongside a PostgreSQL database container, both sharing a podman pod.

1. Clone the quipucords source code repository.
   ```
   git clone git@github.com:quipucords/quipucords.git
   ```
2. Create some directories to share data between your host and containers.
   ```
   mkdir -p "${HOME}"/.local/share/discovery/{data,log,sshkeys}
   ```
3. Build the container image.
   ```
   cd quipucords
   podman login registry.redhat.io
   # complete any login prompts
   podman build -t quipucords .
   ```
4. Create a pod for your containers to share a network.
   ```
   podman pod create --publish 9443:443 qpc-pod
   ```
5. Run a PostgreSQL database container. (optional, but recommended)

   If you are comfortable running PostgreSQL elsewhere on your own, you may skip this step, but you will need to specify your own `QPC_DBMS_*` values later when you run the quipucords container. Alternatively, you can run quipucords with no PostgreSQL database, instead using a local Sqlite file. However, we generally do not recommend using Sqlite as your database.

   If you wish to run PostgreSQL in its own container, run the following command:
   ```
   podman run \
      --name qpc-psql \
      --pod qpc-pod \
      --restart on-failure \
      -e POSTGRES_USER=qpc \
      -e POSTGRES_PASSWORD=qpc \
      -e POSTGRES_DATABASE=qpc-db \
      -v qpc-db-data:/var/lib/pgsql/data \
      -d postgres:12
   ```
   If at some future date you wish to reset your database, then you should stop the `qpc-db` container, remove it, remove its data volume, and recreate it using the previous command.
   ```
   podman stop qpc-psql
   podman rm qpc-psql
   podman volume rm qpc-db-data
   # recreate it using the earlier `podman run ...` command
   ```
   You should to restart the `qpc-server` command after resetting the database or else you will encounter 500 errors when the server cannot find its data.

6. Run the quipucords server container.

   **WARNING**: `podman` on macOS often fails to apply the `z` mount option. If if fails to start with an error like `Error: lsetxattr ... operation not supported`, try removing `:z` from each of the `-v` volume mount definitions.

   ```
   podman run \
      --name qpc-server \
      --restart on-failure \
      --pod qpc-pod \
      -e DJANGO_DEBUG=False \
      -e NETWORK_CONNECT_JOB_TIMEOUT=600 \
      -e NETWORK_INSPECT_JOB_TIMEOUT=10800 \
      -e PRODUCTION=True \
      -e QPC_DBMS_HOST=qpc-psql \
      -e QPC_DBMS_PASSWORD=qpc \
      -e QPC_DBMS_USER=qpc \
      -e QPC_SERVER_TIMEOUT=5 \
      -e QPC_SERVER_USERNAME=admin \
      -e QPC_SERVER_PASSWORD=pleasechangethispassword \
      -e QPC_SERVER_USER_EMAIL=admin@example.com \
      -v "${HOME}"/.local/share/discovery/data/:/var/data:z \
      -v "${HOME}"/.local/share/discovery/log/:/var/log:z \
      -v "${HOME}"/.local/share/discovery/sshkeys/:/sshkeys:z \
      -d quipucords
   ```

   If you decided to use the local Sqlite file instead of PostgreSQL, omit the `QPC_DBMS_*` values and instead specify `-e QPC_DBMS=sqlite`.

   You should now be able to access the quipucords server from your host at `https://0.0.0.0:9443` using the values for `QPC_SERVER_USERNAME` and `QPC_SERVER_PASSWORD` as your login and password in both the CLI and the web UI.

   You may adjust the `QPC_*` values as you like. Note that you must stop and remove the existing `qpc-server` container before changing those values.

   For debugging purposes, may may want to map the `/app` to your local clone of quipucords. To do this, you may want to add an argument like `-v "${HOME}"/projects/quipucords/:/app`. By mapping this directory, you can rapidly change server code without having to rebuild the container.

##  Option 2: Install and run containers with podman compose

You may also use `podman compose` to run quipucords, but please note that the `docker-compose.yml` file included with this repo may not always work for you as-is. Mac users may need to remove `:z` mount bind options. You may also need to change exposed port numbers if they conflict with existing services.

Also note that the current `docker-compose.yml` file (at the time of this writing) enables some experimental settings and additional containers that are not enabled by default and are not yet supported for downstream users.

So, you should proceed with this option _only_ if you really know what you are doing and are confident with your local configuration.

1. Clone the quipucords and quipucords-ui repositories into the same parent directory.
   ```
   git clone git@github.com:quipucords/quipucords.git
   git clone git@github.com:quipucords/quipucords-ui.git
   ```

2. Build the UI in the quipucords directory. See [quipucords-ui installation instructions](https://github.com/quipucords/quipucords-ui) for additional setup information. You must have NodeJS and yarn installed.

   Even though the quipucords `Dockerfile` has instructions to fetch the latest UI assets from GitHub, this step requires you to rebuild the assets locally on your host because the `docker-compose.yml` file instructs the container to mount your host's code into `/app`, and that mounted directory effectively overwrites the existing UI assets that were in the container image.

   On Linux:
   ```
   cd quipucords
   npm install yarn
   make clean-ui build-ui server-static
   ```

   On Mac:
   ```
   cd quipucords
   brew install yarn
   make clean-ui build-ui server-static
   ```
3. Run podman compose:

   For Linux users using Podman instead of Docker, this one-time setup may be necessary:
   ```
   systemctl enable --user podman.socket
   systemctl start --user podman.socket
   # add the next line to your ~/.bashrc (or equivalent)
   export DOCKER_HOST=unix://"${XDG_RUNTIME_DIR}"/podman/podman.sock
   ```
   then run:
   ```
   podman compose up -d
   ```

   For Mac users, just run:
   ```
   podman compose up -d
   ```

   You should now be able to access the quipucords server from your host at `http://0.0.0.0:8080` using the login `admin` and password printed the _first_ time the server starts up (see `podman logs quipucords-qpc-server-1`; the randomly generated password is only printed **once**) in both the CLI and the web UI.

   If at some future date you wish to reset your database, then you may stop the composed containers, remove the db container, and compose up again. Note that the server container will generate a new random password any time it starts if it can find no admin user in its database.

   ```
   podman compose stop
   podman rm quipucords-qpc-db-1
   podman compose up -d
   ```


##  Further steps and configuration

Configure the `qpc` CLI (see [qpc README](https://github.com/quipucords/qpc/blob/main/README.md) for details) to use your running quipucords containers with command like:
```
qpc server config --host 127.0.0.1
qpc server login
```

To enter the container use one of the following commands depending on which method you used:
```
podman exec -it qpc-server bash
podman exec -it quipucords-qpc-server-1 bash
```
