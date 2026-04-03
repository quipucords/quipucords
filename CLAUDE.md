# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

quipucords is a discovery and reporting tool that scans IT environments to identify Red Hat products. It inspects systems using SSH (network scans) and platform APIs (OpenShift, Satellite, Ansible Automation Platform, VMware vCenter, Red Hat Advanced Cluster Security).

The backend is a Django REST API with Celery for asynchronous task processing. Scans collect system information, deduplicate it, fingerprint products, and generate downloadable reports.

## Architecture

### Core Components

- **API Layer** (`quipucords/api/`) - Django REST Framework endpoints organized by resource type:
  - `auth/` - External Authentication and token management
  - `credential/` - Credentials for accessing scan targets
  - `source/` - Data sources (network ranges, vCenter instances, etc.)
  - `scanjob/` - Scan jobs and tasks
  - `*_report/` - Report generation (aggregate, deployments, details, insights)
  - `common/` - Shared API utilities, pagination, serializers

- **Scanner Layer** (`quipucords/scanner/`) - Implements scan execution for each source type:
  - `network/` - SSH-based scans using Ansible playbooks
  - `vcenter/` - VMware vCenter API scans
  - `satellite/` - Red Hat Satellite API scans
  - `openshift/` - OpenShift API scans
  - `ansible/` - Ansible Automation Platform API scans
  - `rhacs/` - Red Hat Advanced Cluster Security API scans
  - `job.py` - Orchestrates ScanTaskRunners and creates reports
  - `tasks.py` - Celery task definitions

- **Fingerprinter** (`quipucords/fingerprinter/`) - Product detection logic:
  - `runner.py` - Processes raw facts and identifies installed products
  - `jboss_*.py` - JBoss product-specific fingerprinting

- **Settings & Config** (`quipucords/quipucords/`) - Django project configuration:
  - `settings.py` - Django settings, database config, secrets management
  - `celery.py` - Celery app configuration and task discovery
  - `environment.py` - Environment variable handling, version info

### Data Flow

1. User creates Credentials and Sources via API
2. User initiates a Scan via ScanJob API
3. ScanJob creates ScanTasks (one per source, plus fingerprint task)
4. Celery workers execute ScanTasks via scanner-specific TaskRunners
5. Scan results stored in InspectResults and ConnectResults
6. FingerprintTaskRunner processes results to identify products
7. Reports generated from fingerprinted data

### Source Types

All source types are defined in `constants.py` as `DataSources` enum:
- `network` - SSH-based network scans
- `vcenter` - VMware vCenter
- `satellite` - Red Hat Satellite
- `openshift` - OpenShift/Kubernetes
- `ansible` - Ansible Automation Platform
- `rhacs` - Red Hat Advanced Cluster Security

Each scanner module (`scanner/{source_type}/`) must implement:
- `ConnectTaskRunner` - Test connectivity
- `InspectTaskRunner` - Gather facts

## Development Setup

### Prerequisites

- Python 3.12+
- uv (https://docs.astral.sh/uv/)
- podman
- make

On macOS, install GNU tools via Homebrew (see README.md for full list):
```sh
brew install make coreutils gnu-sed skopeo rename yq shellcheck
export PATH="/usr/local/opt/coreutils/libexec/gnubin:/usr/local/opt/make/libexec/gnubin:/usr/local/opt/gnu-sed/libexec/gnubin:$PATH"
```

### Initial Setup

```sh
# Start PostgreSQL and Redis containers
make setup-postgres
make setup-redis

# Install Python dependencies
uv sync

# Initialize database and create admin user
read -s QUIPUCORDS_SERVER_PASSWORD
make server-init QUIPUCORDS_SERVER_PASSWORD="${QUIPUCORDS_SERVER_PASSWORD}"
```

### Running Locally

Start the server and worker in separate terminals:

```sh
# Terminal 1: API server
make server-static
make serve

# Terminal 2: Celery worker
make celery-worker
```

Server runs at http://127.0.0.1:8000

### Running the Server

```sh
make serve
```

### Running the Celery Worker

```sh
make celery-worker
```

### Running the UI

```sh
cd ../quipucords-ui
export QUIPUCORDS_SERVER_PROTOCOL=http
export QUIPUCORDS_SERVER_HOST=127.0.0.1
export QUIPUCORDS_SERVER_PORT=8000
echo ""
echo "Starting the Quipucords UI against ${QUIPUCORDS_SERVER_HOST}:${QUIPUCORDS_SERVER_PORT} ..."
echo ""
npm run start:using-server
```

### Database Configuration

By default, uses PostgreSQL container on port 54321. For custom database:

```sh
# PostgreSQL
export QUIPUCORDS_DBMS=postgres
export QUIPUCORDS_DBMS_HOST=localhost
export QUIPUCORDS_DBMS_PORT=5432
export QUIPUCORDS_DBMS_DATABASE=qpc
export QUIPUCORDS_DBMS_USER=qpc
export QUIPUCORDS_DBMS_PASSWORD=qpc

# Or SQLite (for testing only)
export QUIPUCORDS_DBMS=sqlite
```

## Testing

```sh
# Run all unit tests
make test

# Run specific test
uv run pytest path/to/file.py::test_function_name

# Example
uv run pytest quipucords/tests/utils/test_datetime.py::test_average_date_very_large_list

# Coverage report
make test-coverage

# Integration tests (requires configured sources)
make test-integration
```

Test configuration in `pyproject.toml` under `[tool.pytest.ini_options]`:
- Tests run with `--ds=quipucords.settings`
- Network blocked by default (`--block-network`)
- Test database automatically created/destroyed

## Linting

```sh
# Run all linters (ruff, ansible, shellcheck)
make lint

# Ruff only
make lint-ruff
```

Ruff configuration in `pyproject.toml`:
- Enforces PEP8, pydocstyle, import sorting, complexity limits
- Max complexity: 10
- Test files exempt from some rules (S101, PLR2004, etc.)

## Database Migrations

```sh
# Create new migration
make server-makemigrations

# Apply migrations
make server-migrate

# Check if migrations needed
make check-db-migrations-needed
```

Migrations live in `quipucords/api/migrations/`

## Dependency Management

```sh
# Update all dependencies (Python, RPMs, base images)
make update-lockfiles

# Lock Python dependencies only
make lock-requirements

# Check if lockfiles in sync
make check-requirements
```

Uses uv for Python deps. Lockfiles in `lockfiles/`:
- `requirements.txt` - Exported from uv.lock
- `requirements-build.txt` - Build-time deps
- `rpms.lock.yaml` - System package locks

## Container Builds

```sh
# Build quipucords container
make build-container

# Customize tag
make build-container QUIPUCORDS_CONTAINER_TAG=my-tag
```

Containerfile uses multi-stage build (builder + final UBI9 minimal)

## Code Patterns

### Adding a New API Endpoint

1. Create model in `quipucords/api/{resource}/model.py`
2. Create serializer in `quipucords/api/{resource}/serializer.py`
3. Create viewset in `quipucords/api/{resource}/view.py`
4. Register in `quipucords/quipucords/urls.py`
5. Add tests in `quipucords/tests/api/{resource}/`

### Adding a Scanner Feature

1. Implement in scanner module: `quipucords/scanner/{source_type}/`
2. Update TaskRunner classes (ConnectTaskRunner, InspectTaskRunner)
3. For network scans, add Ansible playbook tasks in `scanner/network/runner/`
4. Add tests in `quipucords/tests/scanner/{source_type}/`

### Working with Encrypted Fields

Credentials and sensitive data use `EncryptedTextField` from `api/encrypted_fields.py`:
- Encrypts on save, decrypts on read
- Uses `QUIPUCORDS_ENCRYPTION_SECRET_KEY` env var
- DO NOT log or expose decrypted values

### Celery Tasks

Define tasks in module `tasks.py` and register in `quipucords/quipucords/celery.py`:
```python
task_packages = [
    "scanner",
    "scanner.satellite.six",
    "api.deployments_report.tasks",
    "api.publish.tasks",
]
```

## Environment Variables

Key settings (see `settings.py` and `environment.py` for complete list):

- `QUIPUCORDS_DBMS` - Database type: `postgres` or `sqlite`
- `QUIPUCORDS_DBMS_HOST`, `QUIPUCORDS_DBMS_PORT`, etc. - PostgreSQL config
- `QUIPUCORDS_SESSION_SECRET_KEY` - Django secret (auto-generated if not set)
- `QUIPUCORDS_ENCRYPTION_SECRET_KEY` - Encryption key for credentials
- `QUIPUCORDS_DATA_DIR` - Data directory (default: `./var`)
- `QUIPUCORDS_LOG_LEVEL` - Logging level
- `DJANGO_DEBUG` - Django debug mode (default: False in production)
- `QUIPUCORDS_CELERY_WORKER_MIN_CONCURRENCY` - Celery worker pool size
- `QUIPUCORDS_CELERY_WORKER_MAX_CONCURRENCY` - Max Celery worker pool size

Redis config:
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`

## Debugging

VSCode config for attaching to containers in `.vscode/launch.json`:
```json
{
    "name": "Container attach",
    "type": "python",
    "request": "attach",
    "connect": {"host": "0.0.0.0", "port": 5678},
    "pathMappings": [{"localRoot": "${workspaceFolder}", "remoteRoot": "/app"}]
}
```

## Related Projects

- **qpc** - CLI client (https://github.com/quipucords/qpc)
- **quipucords-ui** - Web UI (https://github.com/quipucords/quipucords-ui)
- **quipucordsctl** - Management tool and installer (https://github.com/quipucords/quipucordsctl)

## Important Notes

- quipucords provides HTTP APIs only; use qpc CLI or quipucords-ui for user interfaces
- Network scans require SSH access with bash shell (not `/sbin/nologin` or `/bin/false`)
- Celery worker must run alongside server for scans to complete
- Scan logs stored in `/var/log` in containers, `var/` directory in local dev
- Feature flags defined in `quipucords/quipucords/featureflag.py`
