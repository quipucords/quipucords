# Installation

##  Installing and running the server and database containers
The quipucords container image can be created from source. This quipucords repository includes a Dockerfile that contains instructions for the image creation of the server.
You must have[Podman installed](https://podman.io/getting-started/installation).

1. Install `podman` if necessary.
   * If running on Fedora/Centos/RHEL,
      ```
      sudo subscription-manager register
      sudo dnf install -y podman
      ```
   * If running on macOS,
      ```
      brew install podman
      podman machine init
      podman machine start
      ```
2. Clone the quipucords source code repository.
   ```
   git clone git@github.com:quipucords/quipucords.git
   ```
3. Create some directories to share data between your host and containers.
   ```
   mkdir -p "${HOME}"/.local/share/discovery/{data,log,sshkeys}
   ```
   **WARNING**: If you are running `podman` on macOS (not Linux), container volume mounts for those directories may fail unexpectedly. You may need to do the following before starting containers:
   ```
   podman machine stop
   podman machine rm
   podman machine init --volume "${HOME}"/.local/share/discovery/
   podman machine start
   ```
4. Build the container image.
   ```
   cd quipucords
   podman login registry.redhat.io
   # complete any login prompts
   podman build -t quipucords .
   ```
5. Create a pod for your containers to share a network.
   ```
   podman pod create --publish 9443:443 qpc-pod
   ```
6. Run a PostgreSQL database container. (optional, but recommended)

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
7. Run the quipucords server container.

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
