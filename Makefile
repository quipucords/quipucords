DATE		= $(shell date)
PYTHON		= $(shell poetry run which python 2>/dev/null || which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords
PIP_COMPILE_ARGS = --no-upgrade
BINDIR  = bin
PARALLEL_NUM ?= $(shell $(PYTHON) -c 'import multiprocessing as m;print(int(max(m.cpu_count()/2, 2)))')
TEST_TIMEOUT ?= 15
TEST_OPTS := -n $(PARALLEL_NUM) -ra -m 'not slow' --timeout=$(TEST_TIMEOUT) --durations=10
QUIPUCORDS_CELERY_WORKER_MIN_CONCURRENCY ?= 10
QUIPUCORDS_CELERY_WORKER_MAX_CONCURRENCY ?= 10

QUIPUCORDS_CONTAINER_TAG ?= quipucords
QUIPUCORDS_UI_PATH ?= ../quipucords-ui
QUIPUCORDS_UI_RELEASE ?= latest
GITHUB_API_TOKEN_SECRET ?= /run/secrets/gh_api_token
GITHUB_API_TOKEN := $(file < $(GITHUB_API_TOKEN_SECRET))
ifneq ($(GITHUB_API_TOKEN),)
	GITHUB_API_AUTH = -H "Authorization: Bearer $(GITHUB_API_TOKEN)"
endif

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                          to show this message"
	@echo "  all                           to execute all following targets (except test)"
	@echo "  celery-worker                 to run the celery worker"
	@echo "  clean                         to remove pyc/cache files"
	@echo "  clean-db                      to remove postgres container / sqlite db"
	@echo "  clean-ui                      to remove UI assets"
	@echo "  lint                          to run all linters"
	@echo "  lint-ruff                     to run ultrafast ruff linter"
	@echo "  lint-ansible                  to run the ansible linter (for now only do syntax check)"
	@echo "  lint-shell                    to run the shellcheck linter"
	@echo "  lock-requirements             to lock all python dependencies"
	@echo "  update-requirements           to update all python dependencies"
	@echo "  check-requirements            to check python dependency files"
	@echo "  test                          to run unit tests"
	@echo "  test-coverage                 to run unit tests and measure test coverage"
	@echo "  swagger-valid                 to run swagger-cli validation"
	@echo "  setup-postgres                to create a default postgres container"
	@echo "  server-init                   to run server initializion steps"
	@echo "  server-set-superuser          to create or update the superuser"
	@echo "  serve                         to run the server with default db"
	@echo "  serve-swagger                 to run the openapi/swagger ui for quipucords"
	@echo "  build-ui                      to build ui and place result in django server"
	@echo "  fetch-ui                      to fetch prebuilt ui and place it in django server"
	@echo "  build-container               to build the container image for quipucords"
	@echo "  check-db-migrations-needed    to check if new migration files are required"

all: lint test-coverage

clean:
	rm -rf .pytest_cache quipucords.egg-info dist build $(shell find . | grep -E '(.*\.pyc)|(\.coverage(\..+)*)$$|__pycache__')

clean-ui:
	rm -rf quipucords/client
	rm -rf quipucords/quipucords/templates
	rm -rf quipucords/staticfiles

clean-db:
	rm -rf quipucords/db.sqlite3
	podman stop quipucords-dev-db || true
	podman rm -f quipucords-dev-db || true
	podman volume rm -f quipucords-dev-db

lock-requirements: lock-main-requirements lock-build-requirements

lock-main-requirements:
	poetry lock --no-update
	poetry export -f requirements.txt --only=main --without-hashes -o requirements.txt

lock-build-requirements:
	poetry run pybuild-deps compile -o requirements-build.txt

update-requirements:
	poetry update --no-cache
	$(MAKE) lock-requirements PIP_COMPILE_ARGS="--upgrade"

check-requirements:
ifeq ($(shell git diff --exit-code requirements.txt >/dev/null 2>&1; echo $$?), 0)
	@exit 0
else
	@echo "requirements.txt not in sync with poetry.lock. Run 'make lock-requirements' and commit the changes"
	@exit 1
endif

test:
	poetry run pytest $(TEST_OPTS)

test-case:
	echo $(pattern)
	$(MAKE) test -e TEST_OPTS="${TEST_OPTS} $(pattern)"

test-coverage:
	# We seem to have encountered a bug with pytest-cov or coverage.
	# We were using --cov-append on each test run, but sometimes it failed and
	# overwrote the .coverage file, resulting in apparent missing test coverage.
	# Our workaround is to explicitly write to separate files and then explicitly
	# combine them to a single .coverage file.
	$(MAKE) test TEST_OPTS="${TEST_OPTS} --cov=quipucords" QUIPUCORDS_DBMS=postgres COVERAGE_FILE=.coverage.notslow
	$(MAKE) test TEST_OPTS="${TEST_OPTS} -m dbcompat --cov=quipucords" QUIPUCORDS_DBMS=sqlite COVERAGE_FILE=.coverage.dbcompat
	$(MAKE) test TEST_OPTS="-n $(PARALLEL_NUM) -ra -m slow --cov=quipucords" COVERAGE_FILE=.coverage.slow
	poetry run coverage combine --keep .coverage.notslow .coverage.dbcompat .coverage.slow
	poetry run coverage report
	# We must run `coverage xml` explicitly to make GitHub codecov action happy.
	poetry run coverage xml

test-integration:
	$(MAKE) test TEST_OPTS="-ra -vvv --disable-warnings -m integration"

swagger-valid:
	node_modules/swagger-cli/swagger-cli.js validate docs/swagger.yml

lint: lint-shell lint-ruff lint-ansible

lint-ruff:
	poetry run ruff check .
	poetry run ruff format --check .

lint-ansible:
	# syntax check playbooks (related roles are loaded and validated as well)
	poetry run ansible-playbook -e variable_host=localhost -c local quipucords/scanner/network/runner/*.yml --syntax-check

lint-shell:
	shellcheck ./deploy/*.sh

server-makemigrations:
	$(PYTHON) quipucords/manage.py makemigrations api --settings quipucords.settings

server-migrate:
	$(PYTHON) quipucords/manage.py migrate --settings quipucords.settings -v 3

server-randomize-sequences:
	$(PYTHON) quipucords/manage.py randomize_db_sequences --settings quipucords.settings

celery-worker:
	$(PYTHON) -m celery --app quipucords --workdir quipucords worker --autoscale=${QUIPUCORDS_CELERY_WORKER_MAX_CONCURRENCY},${QUIPUCORDS_CELERY_WORKER_MIN_CONCURRENCY}

server-set-superuser:
	$(PYTHON) quipucords/manage.py create_or_update_user --settings quipucords.settings -v 3

server-init: server-migrate server-set-superuser

setup-postgres:
	podman run --name quipucords-dev-db --replace \
		-p 54321:5432 \
	  	-e POSTGRESQL_USER=qpc \
      	-e POSTGRESQL_PASSWORD=qpc \
      	-e POSTGRESQL_DATABASE=qpc \
		-v quipucords-dev-db:/var/lib/pgsql/data \
		-itd registry.redhat.io/rhel9/postgresql-15:latest
	sleep 3
	podman exec quipucords-dev-db psql -c 'alter role qpc with CREATEDB'

server-static:
	$(PYTHON) quipucords/manage.py collectstatic --settings quipucords.settings --no-input

serve:
	DJANGO_DEBUG=1 $(PYTHON) quipucords/manage.py runserver --nostatic

$(QUIPUCORDS_UI_PATH):
	@echo "Couldn't find quipucords-ui repo (${QUIPUCORDS_UI_PATH})"
	@echo "Tip: git clone https://github.com/quipucords/quipucords-ui.git ${QUIPUCORDS_UI_PATH}"
	exit 1

build-ui: $(QUIPUCORDS_UI_PATH) clean-ui
	cd $(QUIPUCORDS_UI_PATH);yarn;yarn build
	cp -rf $(QUIPUCORDS_UI_PATH)/dist/client quipucords/client
	cp -rf $(QUIPUCORDS_UI_PATH)/dist/templates quipucords/quipucords/templates

fetch-ui: clean-ui
	@if [[ $(QUIPUCORDS_UI_RELEASE) = "latest" ]]; then \
		GH_FILE=`mktemp`; \
		curl $(GITHUB_API_AUTH) --output "$${GH_FILE}" -sSf "https://api.github.com/repos/quipucords/quipucords-ui/releases/$(QUIPUCORDS_UI_RELEASE)"; \
		DOWNLOAD_URL=`jq -r '.assets[] | select(.name | test("quipucords-ui-dist.tar.gz")) | .browser_download_url' "$${GH_FILE}"`; \
		rm "$${GH_FILE}"; \
	else \
		DOWNLOAD_URL="https://github.com/quipucords/quipucords-ui/releases/download/$(QUIPUCORDS_UI_RELEASE)/quipucords-ui-dist.tar.gz"; \
	fi; \
	echo "download_url=$${DOWNLOAD_URL}"; \
	curl -k -SL "$${DOWNLOAD_URL}" -o ui-dist.tar.gz &&\
	tar -xzvf ui-dist.tar.gz &&\
	mkdir -p quipucords/quipucords/ &&\
	mv dist/templates quipucords/quipucords/. &&\
	mv dist/client quipucords/. &&\
	rm -rf ui-dist* dist

quipucords_on_ui_dir = ${QUIPUCORDS_UI_PATH}/.qpc/quipucords
$(quipucords_on_ui_dir): $(QUIPUCORDS_UI_PATH)
	@echo "Creating quipucords symlink on UI repo"
	mkdir -p $(QUIPUCORDS_UI_PATH)/.quipucords
	ln -sf $(TOPDIR) $(QUIPUCORDS_UI_PATH)/.quipucords/quipucords

serve-swagger: $(quipucords_on_ui_dir)
	cd $(QUIPUCORDS_UI_PATH);yarn;node ./scripts/swagger.js

build-container:
	podman build \
		--build-arg UI_RELEASE=$(QUIPUCORDS_UI_RELEASE) \
		--secret=id=gh_api_token,src=.github_api_token \
		-t $(QUIPUCORDS_CONTAINER_TAG) .

check-db-migrations-needed:
	$(PYTHON) quipucords/manage.py makemigrations --check

generate-sudo-list:
	@$(PYTHON) scripts/generate_sudo_list.py docs "docs/sudo_cmd_list.txt"

test-sudo-list:
	@$(PYTHON) scripts/generate_sudo_list.py compare "docs/sudo_cmd_list.txt" || exit 1
