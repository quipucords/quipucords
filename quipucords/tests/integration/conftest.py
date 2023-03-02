"""Common fixtures for integration tests."""

from urllib.parse import urljoin

import pytest
from pytest_docker_tools import build, container

from tests import constants
from tests.utils.container_wrappers import (
    PostgresContainer,
    QuipucordsContainer,
    ScanTargetContainer,
)
from tests.utils.http import BaseUrlClient, QPCAuth

# pylint: disable=no-value-for-parameter
postgres_container = container(
    environment={
        "POSTGRES_USER": constants.POSTGRES_USER,
        "POSTGRES_PASSWORD": constants.POSTGRES_PASSWORD,
        "POSTGRES_DB": constants.POSTGRES_DB,
    },
    image="postgres:12",
    restart_policy={"Name": "on-failure"},
    scope="class",
    timeout=constants.READINESS_TIMEOUT_SECONDS,
    wrapper_class=PostgresContainer,
)

qpc_server_image = build(
    path=constants.PROJECT_ROOT_DIR.as_posix(),
    rm=constants.CLEANUP_DOCKER_LAYERS,
    forcerm=constants.CLEANUP_DOCKER_LAYERS,
)
qpc_server_container = container(
    environment={
        "ANSIBLE_LOG_LEVEL": constants.QPC_ANSIBLE_LOG_LEVEL,
        "DJANGO_LOG_LEVEL": constants.QUIPUCORDS_LOG_LEVEL,
        "QPC_DBMS": "postgres",
        "QPC_DBMS_DATABASE": constants.POSTGRES_DB,
        "QPC_DBMS_HOST": "{postgres_container.ips.primary}",
        "QPC_DBMS_PASSWORD": constants.POSTGRES_PASSWORD,
        "QPC_DBMS_PORT": 5432,
        "QPC_DBMS_USER": constants.POSTGRES_USER,
        "QPC_SERVER_PASSWORD": constants.QPC_SERVER_PASSWORD,
        "QPC_SERVER_USERNAME": constants.QPC_SERVER_USERNAME,
        "QUIPUCORDS_COMMIT": constants.QPC_COMMIT,
        "QUIPUCORDS_LOG_LEVEL": constants.QUIPUCORDS_LOG_LEVEL,
        "QUIPUCORDS_MANAGER_HEARTBEAT": constants.QUIPUCORDS_MANAGER_HEARTBEAT,
    },
    image="{qpc_server_image.id}",
    ports={"443/tcp": None},
    restart_policy={"Name": "always"},
    scope="class",
    timeout=constants.READINESS_TIMEOUT_SECONDS,
    wrapper_class=QuipucordsContainer,
)

scan_target_image = build(
    buildargs={
        "USERNAME": constants.SCAN_TARGET_USERNAME,
        "PASSWORD": constants.SCAN_TARGET_PASSWORD,
        "SSH_PORT": constants.SCAN_TARGET_SSH_PORT,
    },
    dockerfile="Dockerfile.scan-target",
    path=constants.PROJECT_ROOT_DIR.as_posix(),
)
scan_target_container = container(
    image="{scan_target_image.id}",
    ports={f"{constants.SCAN_TARGET_SSH_PORT}/tcp": None},
    privileged=True,
    restart_policy={"Name": "on-failure"},
    scope="session",
    timeout=constants.READINESS_TIMEOUT_SECONDS,
    wrapper_class=ScanTargetContainer,
)
# pylint: enable=no-value-for-parameter


@pytest.fixture(scope="class")
def apiclient(qpc_server_container: QuipucordsContainer):
    """QPC api client configured make requests to containerized qpc server."""
    client = BaseUrlClient(
        base_url=urljoin(qpc_server_container.server_url, "api/v1/"),
    )
    client.auth = QPCAuth(
        base_url=qpc_server_container.server_url,
        username=constants.QPC_SERVER_USERNAME,
        password=constants.QPC_SERVER_PASSWORD,
    )
    return client


@pytest.fixture(scope="class")
def qpc_client(qpc_server_container: QuipucordsContainer):
    """QPC client configured make requests to containerized qpc server."""
    return BaseUrlClient(
        base_url=qpc_server_container.server_url,
    )
