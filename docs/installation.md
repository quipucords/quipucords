# Installation

Hello world. Please do not merge this.

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
                    -d postgres:12
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
