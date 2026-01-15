PYTHON		= $(shell uv run which python 2>/dev/null || which python)

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
  DEFAULT_CACHE_DIR := $(HOME)/Library/Caches
  # macOS/Darwin's built-in `sed` and `date` are BSD-style and incompatible with Linux/GNU-style arguments.
  # However, macOS users can install GNU sed as `gsed` and GNU date as `gdate` using Homebrew.
  ifneq ($(shell command -v gsed),)
    SED := gsed
  else
    $(info "Warning: gsed may be required on macOS, but it is not installed.")
    $(info "Please run 'brew install gnu-sed' to install it.")
    SED := sed # Fall back to default sed for now
  endif
  ifneq ($(shell command -v gdate),)
    DATE := gdate
  else
    $(info "Warning: gdate may be required on macOS, but it is not installed.")
    $(info "Please run 'brew install coreutils' to install it.")
    DATE := date # Fall back to default date for now
  endif
else
  DEFAULT_CACHE_DIR := $(HOME)/.cache
  SED := sed
  DATE := date
endif
CACHE_DIR := $(shell [ -n "$(XDG_CACHE_HOME)" ] && echo "$(XDG_CACHE_HOME)" || echo "$(DEFAULT_CACHE_DIR)")
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
QUIPUCORDS_POSTGRES_WAIT_TIME ?= 10

UBI_VERSION=9
UBI_IMAGE=registry.access.redhat.com/ubi$(UBI_VERSION)
UBI_MINIMAL_IMAGE=registry.access.redhat.com/ubi$(UBI_VERSION)/ubi-minimal
RPM_LOCKFILE_IMAGE=localhost/rpm-lockfile-prototype

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                          to show this message"
	@echo "  all                           to execute all following targets (except test)"
	@echo "  celery-worker                 to run the celery worker"
	@echo "  clean                         to remove pyc/cache files"
	@echo "  clean-db                      to remove postgres container / sqlite db"
	@echo "  lint                          to run all linters"
	@echo "  lint-ruff                     to run ultrafast ruff linter"
	@echo "  lint-ansible                  to run the ansible linter (for now only do syntax check)"
	@echo "  lint-shell                    to run the shellcheck linter"
	@echo "  lock-requirements             to lock all python dependencies"
	@echo "  lock-rpms  		           to lock all dnf dependencies"
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
	@echo "  build-container               to build the container image for quipucords"
	@echo "  check-db-migrations-needed    to check if new migration files are required"
	@echo "  update-lockfiles		       update all 'lockfiles'"

all: lint test-coverage

clean:
	rm -rf .pytest_cache quipucords.egg-info dist build $(shell find . | grep -E '(.*\.pyc)|(\.coverage(\..+)*)$$|__pycache__')

clean-db:
	rm -rf quipucords/db.sqlite3
	podman stop quipucords-dev-db || true
	podman rm -f quipucords-dev-db || true
	podman volume rm -f quipucords-dev-db

lock-requirements: lock-main-requirements lock-build-requirements

lock-main-requirements:
	uv lock
	uv export --no-emit-project --no-dev --frozen --no-hashes -o lockfiles/requirements.txt

lock-build-requirements:
	uv run pybuild-deps compile lockfiles/requirements.txt -o lockfiles/requirements-build.txt

update-requirements:
	uv lock --upgrade
	$(MAKE) lock-requirements

check-requirements:
ifeq ($(shell git diff --exit-code lockfiles/requirements.txt >/dev/null 2>&1; echo $$?), 0)
	@exit 0
else
	@echo "requirements.txt not in sync with uv.lock. Run 'make lock-requirements' and commit the changes"
	@exit 1
endif

test:
	uv run pytest $(TEST_OPTS)

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
	uv run coverage combine --keep .coverage.notslow .coverage.dbcompat .coverage.slow
	uv run coverage report
	# We must run `coverage xml` explicitly to make GitHub codecov action happy.
	uv run coverage xml

test-integration:
	$(MAKE) test TEST_OPTS="-ra -vvv --disable-warnings -m integration"

swagger-valid:
	node_modules/swagger-cli/swagger-cli.js validate docs/swagger.yml

lint: lint-shell lint-ruff lint-ansible

lint-ruff:
	uv run ruff check .
	uv run ruff format --check .

lint-ansible:
	# syntax check playbooks (related roles are loaded and validated as well)
	uv run ansible-playbook -e variable_host=localhost -c local quipucords/scanner/network/runner/*.yml --syntax-check

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
	sleep $(QUIPUCORDS_POSTGRES_WAIT_TIME)
	podman exec quipucords-dev-db psql -c 'alter role qpc with CREATEDB'

setup-redis:
	podman run --name quipucords-dev-redis --replace \
		-p 6379:6379 \
		-d registry.redhat.io/rhel9/redis-7:latest

server-static:
	$(PYTHON) quipucords/manage.py collectstatic --settings quipucords.settings --no-input

serve:
	DJANGO_DEBUG=1 $(PYTHON) quipucords/manage.py runserver

build-container:
	podman build -t $(QUIPUCORDS_CONTAINER_TAG) .

check-db-migrations-needed:
	$(PYTHON) quipucords/manage.py makemigrations --check

generate-sudo-list:
	@$(PYTHON) scripts/generate_sudo_list.py docs "docs/sudo_cmd_list.txt"

test-sudo-list:
	@$(PYTHON) scripts/generate_sudo_list.py compare "docs/sudo_cmd_list.txt" || exit 1

# prepare rpm-lockfile-prototype tool to lock our rpms
setup-rpm-lockfile:
	latest_digest=$$(skopeo inspect --raw "docker://$(UBI_IMAGE):latest" | sha256sum | cut -d ' ' -f1); \
	curl https://raw.githubusercontent.com/konflux-ci/rpm-lockfile-prototype/refs/heads/main/Containerfile | \
		podman build -t $(RPM_LOCKFILE_IMAGE) \
		--build-arg "BASE_IMAGE=$(UBI_IMAGE)@sha256:$${latest_digest}" -

setup-rpm-lockfile-if-needed:
ifneq ($(shell podman image exists $(RPM_LOCKFILE_IMAGE) >/dev/null 2>&1; echo $$?), 0)
	$(MAKE) setup-rpm-lockfile
else
	$(eval image_created_at=$(shell $(DATE) -d $$(podman inspect --format '{{json .Created}}' $(RPM_LOCKFILE_IMAGE) | tr -d '"') +"%s"))
	$(eval 36h_ago=$(shell $(DATE) -d "36 hours ago" +"%s"))
	# recreate the rpm-lockfile container if it is "old"
	@if [ "$(image_created_at)" -lt "$(36h_ago)" ]; then \
		$(MAKE) setup-rpm-lockfile; \
	fi
endif

# update rpm locks
lock-rpms: setup-rpm-lockfile-if-needed
	# the last layer will be considered the base image here; 
	$(eval BASE_IMAGE=$(shell grep '^FROM ' Containerfile | tail -n1 | cut -d" " -f2))
	# extract ubi.repo from BASE_IMAGE
	# lots of sed substitutions requred because ubi images don't have the ubi.repo formatted in the way 
	# the EC checks expect
	# https://github.com/release-engineering/rhtap-ec-policy/blob/main/data/known_rpm_repositories.yml
	# more about this on downstream konflux docs https://url.corp.redhat.com/d54f834
	podman run -it --rm "$(BASE_IMAGE)" cat /etc/yum.repos.d/ubi.repo | \
		$(SED) 's/ubi-$(UBI_VERSION)-codeready-builder-\([[:alnum:]-]*rpms\)/codeready-builder-for-ubi-$(UBI_VERSION)-$$basearch-\1/g' | \
		$(SED) 's/ubi-$(UBI_VERSION)-\([[:alnum:]-]*rpms\)/ubi-$(UBI_VERSION)-for-$$basearch-\1/g' | \
		$(SED) 's/\r$$//' > lockfiles/ubi.repo
	# finally, update the rpm locks
	# RPMDB_CACHE => rpm-lockfile-prototype has an undocumented cache
	# https://github.com/konflux-ci/rpm-lockfile-prototype/blob/283ee2cd7938a2142d8ac98de33ba0d0e3ac146f/rpm_lockfile/utils.py#L18C1-L18C11
	RPMDB_CACHE_PATH="$(CACHE_DIR)/rpm-lockfile-prototype"; \
	mkdir -p "$${RPMDB_CACHE_PATH}"; \
	podman run -w /workdir --rm \
		-v $(TOPDIR):/workdir:Z \
		-v "$${RPMDB_CACHE_PATH}:/root/.cache/rpm-lockfile-prototype:Z" \
		$(RPM_LOCKFILE_IMAGE):latest \
		--image $(BASE_IMAGE) \
		--outfile=/workdir/lockfiles/rpms.lock.yaml \
		rpms.in.yaml

# update image digest
.PHONY: lock-baseimages
lock-baseimages:
	separator="================================================================"; \
	baseimages=($$(grep '^FROM ' Containerfile | sed 's/FROM\s*\(.*\)@.*/\1/g' | sort -u)); \
	for image in $${baseimages[@]}; do \
		echo "$${separator}"; \
		echo "updating $${image}..."; \
		# escape "/" for use in $(SED) later \
		escaped_img=$$(echo $${image} | $(SED) 's/\//\\\//g') ;\
		# extract the image digest \
		updated_sha=$$(skopeo inspect --raw "docker://$${image}:latest" | sha256sum | cut -d ' ' -f1); \
		# update Containerfile with the new digest \
		$(SED) -i "s/^\(FROM $${escaped_img}@sha256:\)[[:alnum:]]*/\1$${updated_sha}/g" Containerfile; \
	done; \
	echo "$${separator}"

update-lockfiles: lock-baseimages lock-rpms update-requirements
