DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords

BINDIR  = bin

OMIT_PATTERNS = */test*.py,*/manage.py,*/apps.py,*/wsgi.py,*/settings.py,*/migrations/*,*/docs/*,*/client/*,*/deploy/*

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help           to show this message"
	@echo "  all            to to execute all following targets (except test)"
	@echo "  lint           to run all linters"
	@echo "  lint-flake8    to run the flake8 linter"
	@echo "  lint-pylint    to run the pylint linter"
	@echo "  test           to run unit tests"
	@echo "  test-coverage  to run unit tests and measure test coverage"
	@echo "  swagger-valid  to run swagger-cli validation"
	@echo "  server-init    to run server initializion steps"
	@echo "  serve          to run the server"
	@echo "  manpage        to build the manpage"
	@echo "  html           to build the docs"

all: build lint test-coverage

build: clean-cli
	$(PYTHON) setup.py build -f

clean-cli:
	-rm -rf dist/ build/ quipucords.egg-info/

clean: clean-cli
	rm -rf quipucords/api/migrations/ quipucords/db.sqlite3

install: build
	$(PYTHON) setup.py install -f

test:
	QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True $(PYTHON) quipucords/manage.py test -v 2 quipucords/ qpc/

test-case:
	echo $(pattern)
	QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True $(PYTHON) quipucords/manage.py test -v 2 quipucords/ qpc/ -p $(pattern)

test-coverage:
	QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True coverage run --source=quipucords/,qpc/ quipucords/manage.py test -v 2 quipucords/ qpc/
	coverage report -m --omit $(OMIT_PATTERNS)

swagger-valid:
	node_modules/swagger-cli/bin/swagger-cli.js validate docs/swagger.yml

lint-flake8:
	flake8 . --ignore D203 --exclude quipucords/api/migrations,docs,build,.vscode,client,venv,deploy

lint-pylint:
	find . -name "*.py" -not -name "*0*.py" -not -path "./build/*" -not -path "./docs/*" -not -path "./.vscode/*" -not -path "./client/*" -not -path "./venv/*" -not -path "./deploy/*" | xargs $(PYTHON) -m pylint --load-plugins=pylint_django --disable=duplicate-code

lint: lint-flake8 lint-pylint

server-makemigrations:
	$(PYTHON) quipucords/manage.py makemigrations api --settings quipucords.settings

server-migrate:
	$(PYTHON) quipucords/manage.py migrate --settings quipucords.settings -v 3

server-set-superuser:
	echo "from django.contrib.auth.models import User; admin_not_present = User.objects.filter(email='admin@example.com').count() == 0;User.objects.create_superuser('admin', 'admin@example.com', 'pass') if admin_not_present else print('admin present');print(User.objects.filter(email='admin@example.com'))" | $(PYTHON) quipucords/manage.py shell --settings quipucords.settings -v 3

server-init: server-makemigrations server-migrate server-set-superuser

server-static:
	$(PYTHON) quipucords/manage.py collectstatic --settings quipucords.settings --no-input

serve:
	$(PYTHON) quipucords/manage.py runserver

html:
	@cd docs; $(MAKE) html

manpage:
	@mkdir -p build
	pandoc docs/source/man.rst \
	  --standalone -t man -o build/qpc.1 \
	  --variable=section:1 \
	  --variable=date:'March 18, 2018' \
	  --variable=footer:'version 0.0.42' \
	  --variable=header:'QPC Command Line Guide'
