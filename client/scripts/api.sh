#!/usr/bin/env bash
#
#
# main()
#
{
  PORT=8080
  FILE="$(pwd)/swagger.yaml"
  CONTAINER="palo/swagger-api-mock"

  while getopts p:f: option;
    do
      case $option in
        p ) PORT=$OPTARG;;
        f ) FILE=${OPTARG// };;
      esac
  done

  if [ -z "$(docker info | grep Containers)" ]; then
    exit 1
  fi

  if [ -z "$(docker images | grep $CONTAINER)" ]; then
    echo "Setting up Docker API container"
    docker pull $CONTAINER
  fi

  if [ ! -f $FILE ]; then
    echo "Swagger API file not found, exiting..."
    exit 0
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ]; then
    echo "Starting API..."
    docker run -d --rm -p $PORT:8000 -v $FILE:/data/swagger.yaml $CONTAINER >/dev/null
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Mock API running: http://localhost:$PORT/"
  fi

  echo ""
}

