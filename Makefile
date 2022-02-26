DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords
TEST_OPTS := -n auto -ra
QPC_COMPARISON_REVISION = a362b28db064c7a4ee38fe66685ba891f33ee5ba

BINDIR  = bin

QUIPUCORDS_UI_PATH = ../quipucords-ui

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
	PYTHONHASHSEED=0 QUIPUCORDS_MANAGER_HEARTBEAT=1 QPC_DISABLE_AUTHENTICATION=True PYTHONPATH=`pwd`/quipucords \
	pytest $(TEST_OPTS)

test-case:
	echo $(pattern)
	$(MAKE) test -e TEST_OPTS="${TEST_OPTS} $(pattern)"

test-coverage:
	$(MAKE) test TEST_OPTS="${TEST_OPTS} --cov=quipucords" 

swagger-valid:
	node_modules/swagger-cli/swagger-cli.js validate docs/swagger.yml

lint-flake8:
	git diff $(QPC_COMPARISON_REVISION) | flakeheaven lint --diff .

lint-black:
	darker --check --diff --revision $(QPC_COMPARISON_REVISION) .

lint: lint-black lint-flake8

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
	cd $(QUIPUCORDS_UI_PATH);yarn;yarn build
	cp -rf $(QUIPUCORDS_UI_PATH)/dist/client quipucords/client
	cp -rf $(QUIPUCORDS_UI_PATH)/dist/templates quipucords/quipucords/templates
