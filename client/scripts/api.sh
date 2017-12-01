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

  if [ -z "$(which docker)" ]; then
    echo "Setting up API Docker container"
    docker pull $CONTAINER
  fi

  if [ ! -f $FILE ]; then
    echo "Swagger API file not found, exiting..."
    exit 0
  fi

  docker run -i --rm -p $PORT:8000 -v $FILE:/data/swagger.yaml -t $CONTAINER >/dev/null
  exit 0
}

