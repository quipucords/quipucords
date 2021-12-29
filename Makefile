DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords

BINDIR  = bin

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                to show this message"
	@echo "  all                 to execute all following targets (except test)"
	@echo "  lint                to run all linters"
	@echo "  clean               to remove postgres docker container"
	@echo "  lint-flake8         to run the flake8 linter"
	@echo "  lint-pylint         to run the pylint linter"
	@echo "  test                to run unit tests"
	@echo "  test-coverage       to run unit tests and measure test coverage"
	@echo "  swagger-valid       to run swagger-cli validation"
	@echo "  setup-postgres      to create a default postgres container"
	@echo "  server-init         to run server initializion steps"
	@echo "  serve               to run the server with default db"
	@echo "  manpage             to build the manpage"
	@echo "  build-ui       to build ui and place result in django server"

all: lint test-coverage

clean:
	rm -rf quipucords/db.sqlite3
	docker rm -f qpc-db
	rm -rf quipucords/client
	rm -rf quipucords/quipucords/templates

test:
	PYTHONHASHSEED=0 QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True PYTHONPATH=`pwd`/quipucords pytest -ra -n auto

test-case:
	echo $(pattern)
	QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True $(PYTHON) quipucords/manage.py test -v 2 quipucords/ -p $(pattern)

test-coverage:
	PYTHONHASHSEED=0 QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True PYTHONPATH=`pwd`/quipucords pytest -ra -n auto --cov=quipucords

swagger-valid:
	node_modules/swagger-cli/swagger-cli.js validate docs/swagger.yml

lint-flake8:
	flake8 . --ignore D203,W504,W605 --exclude quipucords/api/migrations,docs,build,.vscode,client,venv,deploy,quipucords/local_gunicorn.conf.py

lint-pylint:
	find . -name "*.py" -not -name "*0*.py" -not -path "./build/*" -not -path "./docs/*" -not -path "./.vscode/*" -not -path "./client/*" -not -path "./venv/*" -not -path "./deploy/*" -not -path "./quipucords/local_gunicorn.conf.py" | DJANGO_SETTINGS_MODULE=quipucords.settings xargs $(PYTHON) -m pylint --load-plugins=pylint_django --disable=duplicate-code,wrong-import-order,useless-import-alias,unnecessary-pass,too-many-lines,raise-missing-from

lint: lint-flake8 lint-pylint

server-makemigrations:
	$(PYTHON) quipucords/manage.py makemigrations api --settings quipucords.settings

server-migrate:
	$(PYTHON) quipucords/manage.py migrate --settings quipucords.settings -v 3

server-set-superuser:
	cat ./deploy/setup_user.py | python quipucords/manage.py shell --settings quipucords.settings -v 3

server-init: server-migrate server-set-superuser

setup-postgres:
	docker run --name qpc-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:14.1

server-static:
	$(PYTHON) quipucords/manage.py collectstatic --settings quipucords.settings --no-input

serve:
	$(PYTHON) quipucords/manage.py runserver --nostatic

build-ui:
	cd ../quipucords-ui;yarn;yarn build
	cp -rf ../quipucords-ui/dist/client quipucords/client
	cp -rf ../quipucords-ui/dist/templates quipucords/quipucords/templates
