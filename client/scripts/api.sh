#!/usr/bin/env bash
#
#
# Check if a container is running. Currently supporting the mockApi container
checkContainerRunning()
{
  local CONTAINER=$1
  local FILE=$2
  local COUNT=1
  local DURATION=10
  local DELAY=0.1

  printf "Check container running..."

  while [ $COUNT -le $DURATION ]; do
    sleep $DELAY
    (( COUNT++ ))
    if [ -z "$(docker ps | grep $CONTAINER)" ]; then
      break
    fi
  done

  if [ ! -z "$(docker ps | grep $CONTAINER)" ]; then
    printf "\e[32mContainer SUCCESS"
    printf "\n\n\e[39m"
  else
    local HASH=$(git rev-list -1 --all --abbrev-commit $FILE)
    local COMMIT=$(git rev-list -1 --all --oneline $FILE)
    local BLAME=$(git blame $FILE | grep $HASH | sed 's/^/  /')
    local GITHUB="https://github.com/quipucords/quipucords/commit/$HASH"

    echo "Last Commit:\n\n  $COMMIT\n\nVisit:\n\n  $GITHUB\n\nAssigning Blame:\n\n$BLAME"  > api-debug.txt

    printf "\e[31mContainer ERROR"
    printf "\n\e[31m  Review the Swagger doc for errors."
    printf "\n\e[31m  Last commit: $COMMIT"
    printf "\n\e[31m  See api-debug.txt for details."
    printf "\n\e[31m  Visit: $GITHUB"
    printf "\e[39m\n"
  fi
}
#
#
# Install & Run Quipucords API Mock Container
#
devApi()
{
  local CONTAINER="palo/swagger-api-mock"
  local NAME="quipucords-dev"
  local PORT=$1
  local FILE=$2
  local UPDATE=$3

  docker stop -t 0 $NAME >/dev/null

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up development Docker API container"
    docker pull $CONTAINER
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting development API..."
    docker run -d --rm -p $PORT:8000 -v "$FILE:/data/swagger.yaml" --name $NAME $CONTAINER >/dev/null
  fi

  if [ "$UPDATE" = false ]; then
    checkContainerRunning $CONTAINER $FILE
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Development API running: http://localhost:$PORT/"
    printf "  To stop: $ \e[32mdocker stop $NAME\e[39m\n"
  fi
}
#
#
# Install & Run Quipucords API Container
#
stageApi()
{
  local CONTAINER="quipucords-stage"
  local NAME="quipucords-stage"
  local PORT=$1
  local DIR=$2
  local UPDATE=$3

  docker stop -t 0 $NAME >/dev/null

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up staging Docker API container"
    (cd ../. && make clean)
    docker build -t $CONTAINER ../.
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting staging API..."
    docker run -d --rm -p $PORT:443 -v $DIR:/app/quipucords/client:cached -v $DIR:/app/quipucords/quipucords/templates/client:cached --name $NAME $CONTAINER >/dev/null
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Stage API running: https://localhost:$PORT/"
    echo "  Connected to local directory: $(basename $DIR | cut -c 1-80)"
    printf "  To stop: $ \e[32mdocker stop $NAME\e[39m\n"
  fi
}
#
#
# Install & Run Quipucords API Container
#
prodApi()
{
  local CONTAINER="quipucords-latest"
  local NAME="quipucords"
  local PORT=$1
  local UPDATE=$2

  docker stop -t 2 $NAME >/dev/null

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up production Docker API container"
    (cd ../. && make clean)
    docker build -t $CONTAINER ../.
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting production API..."
    docker run -d --rm -p $PORT:443 --name $NAME $CONTAINER >/dev/null
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Production API running: https://localhost:$PORT/"
    printf "  To stop: $ \e[32mdocker stop $NAME\e[39m\n"
  fi
}
#
#
# main()
#
{
  PORT=8080
  FILE="$(pwd)/swagger.yaml"
  UPDATE=false
  DIR=""

  while getopts p:f:d:t:u option;
    do
      case $option in
        p ) PORT=$OPTARG;;
        f ) FILE="$OPTARG";;
        d ) DIR="$OPTARG";;
        t ) TYPE="$OPTARG";;
        u ) UPDATE=true;;
      esac
  done

  if [ -z "$(docker info | grep Containers)" ]; then
    exit 1
  fi

  case $TYPE in
    prod )
      prodApi $PORT $UPDATE;;
    stage )
      stageApi $PORT $DIR $UPDATE;;
    dev )
      devApi $PORT "$FILE" $UPDATE;;
    * )
      devApi $PORT "$FILE" $UPDATE;;
  esac

  echo ""
}
