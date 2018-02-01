#!/usr/bin/env bash
#
#
# Check container running
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
# Install & Run Quipucords API Mock
#
mockApi()
{
  local CONTAINER="palo/swagger-api-mock"
  local PORT=$1
  local FILE=$2
  local UPDATE=$3

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up Docker Mock API container"
    docker pull $CONTAINER
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting API..."
    docker run -d --rm -p $PORT:8000 -v "$FILE:/data/swagger.yaml" --name quipucords-mock $CONTAINER >/dev/null
  fi

  checkContainerRunning $CONTAINER $FILE

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Mock API running: http://localhost:$PORT/"
    echo "  To stop: $ docker stop quipucords-mock"
  fi
}
#
#
# Install & Run Quipucords API
#
api()
{
  local CONTAINER="quipucords"
  local PORT=$1
  local UPDATE=$2

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up Docker API container"
    docker build -t $CONTAINER ../.
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting API..."
    docker run -d --rm -p $PORT:8000 --name $CONTAINER $CONTAINER >/dev/null
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  API running: http://localhost:$PORT/"
    echo "  To stop: $ docker stop $CONTAINER"
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

  while getopts p:f:u option;
    do
      case $option in
        p ) PORT=$OPTARG;;
        f ) FILE="$OPTARG";;
        u ) UPDATE=true;;
      esac
  done

  if [ -z "$(docker info | grep Containers)" ]; then
    exit 1
  fi

  docker stop -t 3 quipucords >/dev/null
  docker stop -t 0 quipucords-mock >/dev/null

  if [ -f "$FILE" ]; then
    mockApi $PORT "$FILE" $UPDATE
  else
    api $PORT $UPDATE
  fi

  echo ""
}

