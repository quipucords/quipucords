"""Test constants."""

from __future__ import annotations

from pathlib import Path

from tests.env import BaseURI, EnvVar, as_bool

PROJECT_ROOT_DIR = Path(__file__).absolute().parent.parent.parent

CLEANUP_DOCKER_LAYERS = False
FILENAME_AGGREGATE_JSON = "aggregate-{report_id}.json"
FILENAME_DEPLOYMENTS_CSV = "deployments-{report_id}.csv"
FILENAME_DEPLOYMENTS_JSON = "deployments-{report_id}.json"
FILENAME_DETAILS_CSV = "details-{report_id}.csv"
FILENAME_DETAILS_JSON = "details-{report_id}.json"
FILENAME_SHA256SUM = "SHA256SUM"
POSTGRES_DB = "qpc-db"
POSTGRES_PASSWORD = "qpc"
POSTGRES_USER = "qpc"
QUIPUCORDS_LOG_LEVEL = "INFO"
READINESS_TIMEOUT_SECONDS = 60
SCAN_TARGET_PASSWORD = "super-secret-password"
SCAN_TARGET_SSH_PORT = "2222"
SCAN_TARGET_USERNAME = "non-root-user"
VCR_CASSETTES_DIR = PROJECT_ROOT_DIR / "quipucords/tests/cassettes"
# For URI's standard ports 80 and 443, we do not specify those in the VCR
# Request URI's, i.e. accessing external routes, the 443 is not specified,
# so we drop the ports when we rewrite the request URI's in the cassettes.
VCR_NO_PORT_URI_PORTS = [80, 443]


class ConstantsFromEnv:
    """
    Constants from env vars.

    Environment variable names match the attribute name.
    """

    TEST_OCP_AUTH_TOKEN = EnvVar("<AUTH_TOKEN>")
    TEST_OCP_SSL_VERIFY = EnvVar("true", as_bool)
    TEST_OCP_URI = EnvVar("https://fake.ocp.host:9872", BaseURI)
    TEST_OCP_METRICS_URI = EnvVar(
        "https://prometheus-k8s-openshift-monitoring.apps.fake.ocp.host", BaseURI
    )


class VCRPath:
    """
    Descriptor that generates a paths intended for VCR cassettes.

    The path will be based only on VCRPath parent attribute name, which
    should have at least two "words" separated by "_". The first word will
    be considered a folder and the rest will be considered a file name which will
    receive a ".yaml" suffix.

    To give a pratical usage example:

    >>>class Cassettes:
    ...    JUST_AN_EXAMPLE = VCRPath()
    ...
    >>>print(Cassettes.JUST_AN_EXAMPLE)
    '<path/to/quipucords>/tests/cassettes/just/an_example.yaml'
    """

    def __get__(self, obj, objectype=None):
        """Return absolute path to VCRPath."""
        return str(self._path)

    def __set_name__(self, obj, name):
        """Create VCRPath file based on its parent attribute name."""
        folder_name, file_name = name.lower().split("_", 1)
        self._path = VCR_CASSETTES_DIR / f"{folder_name}/{file_name}.yaml"


class VCRCassettes:
    """Paths to VCR cassettes."""

    OCP_DISCOVERER_CACHE = VCRPath()
    OCP_UNAUTHORIZED = VCRPath()
    OCP_CLUSTER = VCRPath()
    OCP_NODE = VCRPath()
    OCP_PODS = VCRPath()
    OCP_CLUSTER_OPERATORS = VCRPath()
    OCP_ROUTE = VCRPath()
    OCP_METRICS_CACHE = VCRPath()
    OCP_SUBSCRIPTIONS = VCRPath()
    OCP_CSV = VCRPath()
    OCP_ACM = VCRPath()
