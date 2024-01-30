"""Misc utils for quipucords."""
import json
from functools import cache

from django.conf import settings


def load_json_from_tarball(json_filename, tarball):
    """Extract a json as dict from given TarFile interface."""
    return json.loads(tarball.extractfile(json_filename).read())


def product_name_to_id(name):
    """Given a product name, return its ID."""
    for prod in products_list():
        if prod["name"] == name:
            return prod["id"]
    return None


@cache
def products_list():
    """Cache and Returns the products list."""
    prods_file = settings.DOCS_DIR / "products-prod.json"
    return json.loads(prods_file.read_text())["products"]
