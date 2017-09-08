DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords

BINDIR  = bin

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

all: build tests-coverage

build: clean
	$(PYTHON) setup.py build -f

clean:
	-rm -rf dist/ build/

install: build
	$(PYTHON) setup.py install -f

test:
	$(PYTHON) quipucords/manage.py test

test-coverage:
	coverage run --source=quipucords/ 	quipucords/manage.py test -v 2;coverage report -m

lint-flake8:
	flake8 . --ignore D203

lint-pylint:
	pylint --disable=duplicate-code */*.py

lint: lint-flake8 lint-pylint

server-init:
	$(PYTHON) quipucords/manage.py makemigrations; $(PYTHON) quipucords/manage.py migrate

serve:
	$(PYTHON) quipucords/manage.py runserver
