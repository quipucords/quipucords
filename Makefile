DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords

BINDIR  = bin

OMIT_PATTERNS = */test*.py,*/manage.py,*/apps.py,*/wsgi.py,*/es_receiver.py,*/settings.py,*/migrations/*,*/docs/*,*/client/*

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help           to show this message"
	@echo "  all            to to execute all following targets (except test)"
	@echo "  lint           to run all linters"
	@echo "  lint-flake8    to run the flake8 linter"
	@echo "  lint-pylint    to run the pylint linter"
	@echo "  test           to run unit tests"
	@echo "  test-coverage  to run unit tests and measure test coverage"
	@echo "  server-init    to run server initializion steps"
	@echo "  serve          to run the server"
	@echo "  manpage        to build the manpage"

all: build lint test-coverage

build: clean-cli
	$(PYTHON) setup.py build -f

clean-cli:
	-rm -rf dist/ build/ quipucords.egg-info/

clean: clean-cli
	rm -rf quipucords/api/migrations/*;rm quipucords/db.sqlite3

install: build
	$(PYTHON) setup.py install -f

test:
	$(PYTHON) quipucords/manage.py test -v 2 quipucords/ qpc/

test-case:
	echo $(pattern)
	$(PYTHON) quipucords/manage.py test -v 2 quipucords/ qpc/ -p $(pattern)

test-coverage:
	coverage run --source=quipucords/,qpc/ quipucords/manage.py test -v 2 quipucords/ qpc/
	coverage report -m --omit $(OMIT_PATTERNS)

lint-flake8:
	flake8 . --ignore D203 --exclude quipucords/api/migrations,docs,build,.vscode,client,venv

lint-pylint:
	find . -name "*.py" -not -name "*0*.py" -not -path "./build/*" -not -path "./docs/*" -not -path "./.vscode/*" -not -path "./client/*" -not -path "./venv/*" | xargs $(PYTHON) -m pylint --load-plugins=pylint_django --disable=duplicate-code

lint: lint-flake8 lint-pylint

server-init:
	$(PYTHON) quipucords/manage.py makemigrations api; $(PYTHON) quipucords/manage.py migrate

serve:
	$(PYTHON) quipucords/manage.py runserver

manpage:
	@mkdir -p build
	pandoc docs/source/man.rst \
	  --standalone -t man -o build/qpc.1 \
	  --variable=section:1 \
	  --variable=date:'November 14, 2017' \
	  --variable=footer:'version 0.0.1' \
	  --variable=header:'QPC Command Line Guide'
