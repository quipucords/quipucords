from logging import getLogger

logger = getLogger(__name__)

from requests.auth import HTTPBasicAuth

from tests.utils.http import BaseUrlClient


class AnsibleControllerApi(BaseUrlClient):
    @classmethod
    def from_connection_info(
        cls, *, host, protocol, port, username, password, ssl_verify: bool = True
    ):
        base_uri = f"{protocol}://{host}:{port}"
        auth = HTTPBasicAuth(username=username, password=password)
        return cls(base_url=base_uri, verify=ssl_verify, auth=auth)
