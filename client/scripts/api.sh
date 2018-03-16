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
    printf "${GREEN}Container SUCCESS"
    printf "\n\n${NOCOLOR}"
  else
    local HASH=$(git rev-list -1 --all --abbrev-commit $FILE)
    local COMMIT=$(git rev-list -1 --all --oneline $FILE)
    local BLAME=$(git blame $FILE | grep $HASH | sed 's/^/  /')
    local GITHUB="https://github.com/quipucords/quipucords/commit/$HASH"

    echo "Last Commit:\n\n  ${COMMIT}\n\nVisit:\n\n  ${GITHUB}\n\nAssigning Blame:\n\n${BLAME}"  > api-debug.txt

    printf "${RED}Container ERROR"
    printf "\n${RED}  Review the Swagger doc for errors."
    printf "\n${RED}  Last commit: ${COMMIT}"
    printf "\n${RED}  See api-debug.txt for details."
    printf "\n${RED}  Visit: ${GITHUB}"
    printf "${NOCOLOR}\n"
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
    printf "  To stop: $ ${GREEN}docker stop ${NAME}${NOCOLOR}\n"
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
  local DATA=$3
  local UPDATE=$4
  local DATA_VOLUME="/var/data"
  local CLIENT_VOLUME="/app/quipucords/client"
  local TEMPLATE_VOLUME="/app/quipucords/quipucords/templates/client"

  docker stop -t 0 $NAME >/dev/null

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up staging Docker API container"
    (cd ../. && make clean)
    docker build -t $CONTAINER ../.
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting staging API..."
    docker run -d --rm -p $PORT:443 -v $DATA:$DATA_VOLUME -v $DIR:$CLIENT_VOLUME:cached -v $DIR:$TEMPLATE_VOLUME:cached --name $NAME $CONTAINER >/dev/null
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Stage API running: https://localhost:${PORT}/"
    echo "  Connected to local directory: $(basename $DIR | cut -c 1-80)"
    printf "  To stop: $ ${GREEN}docker stop ${NAME}${NOCOLOR}\n"
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
  local DATA=$2
  local UPDATE=$3
  local DATA_VOLUME="/var/data"

  docker stop -t 2 $NAME >/dev/null

  if [ -z "$(docker images | grep ^$CONTAINER' ')" ] || [ "$UPDATE" = true ]; then
    echo "Setting up production Docker API container"
    (cd ../. && make clean)
    docker build -t $CONTAINER ../.
  fi

  if [ -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "Starting production API..."
    docker run -d --rm -p $PORT:443 -v $DATA:$DATA_VOLUME --name $NAME $CONTAINER >/dev/null
  fi

  if [ ! -z "$(docker ps | grep $CONTAINER)" ] && [ "$UPDATE" = false ]; then
    echo "  Container: $(docker ps | grep $CONTAINER | cut -c 1-80)"
    echo "  Production API running: https://localhost:${PORT}/"
    printf "  To stop: $ ${GREEN}docker stop ${NAME}${NOCOLOR}\n"
  fi
}
#
#
# main()
#
{
  RED="\e[31m"
  GREEN="\e[32m"
  NOCOLOR="\e[39m"
  PORT=8080
  FILE="$(pwd)/swagger.yaml"
  UPDATE=false
  DIR=""
  DATA="$(pwd)/.container"
  CLEAN=false

  while getopts p:f:d:s:t:cu option;
    do
      case $option in
        p ) PORT=$OPTARG;;
        f ) FILE="$OPTARG";;
        d ) DIR="$OPTARG";;
        s ) DATA="$OPTARG";;
        t ) TYPE="$OPTARG";;
        c ) CLEAN=true;;
        u ) UPDATE=true;;
      esac
  done

  if [ -z "$(docker info | grep Containers)" ]; then
    exit 1
  fi

  if [ "$TYPE" != dev ] && [ "$CLEAN" = true ]; then
    echo "Cleaning Docker and data..."
    printf "${RED}\n"
    docker system prune -f
    printf "${GREEN}Docker cleaning success.${NOCOLOR}\n"
    rm -rf $DATA
  fi

  if [ "$TYPE" != dev ]; then
    mkdir -p $DATA
  fi

  case $TYPE in
    prod )
      prodApi $PORT $DATA $UPDATE;;
    stage )
      stageApi $PORT $DIR $DATA $UPDATE;;
    dev )
      devApi $PORT "$FILE" $UPDATE;;
    * )
      devApi $PORT "$FILE" $UPDATE;;
  esac

  echo ""
}
