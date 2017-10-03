DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords

BINDIR  = bin

OMIT_PATTERNS = */test*.py,*/manage.py,*/apps.py,*/wsgi.py

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

all: build lint test-coverage

build: clean
	$(PYTHON) setup.py build -f

clean:
	-rm -rf dist/ build/ quipucords.egg-info/

install: build
	$(PYTHON) setup.py install -f

test:
	$(PYTHON) quipucords/manage.py test -v 2 quipucords/ qpc/

test-coverage:
	coverage run --source=quipucords/,qpc/ quipucords/manage.py test -v 2 quipucords/ qpc/;coverage report -m --omit $(OMIT_PATTERNS)

lint-flake8:
	flake8 . --ignore D203

lint-pylint:
	find . -name "*.py" | xargs $(PYTHON) -m pylint --load-plugins=pylint_django --disable=duplicate-code

lint: lint-flake8 lint-pylint

server-init:
	$(PYTHON) quipucords/manage.py makemigrations api; $(PYTHON) quipucords/manage.py migrate

serve:
	$(PYTHON) quipucords/manage.py runserver
