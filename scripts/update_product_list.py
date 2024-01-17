"""Script to update the json subset of the RedHat product list."""
import argparse
import csv
import io
import json
import sys
from pathlib import Path

import requests
import urllib3

PRODUCTS_URL = "https://git.app.eng.bos.redhat.com/git/rcm/rcm-metadata.git/plain/cdn/products-prod.csv"


def update_products_json(prod_jsonfile):
    """Download the latest product CSV file and update the JSON subset we use."""
    products_list = []
    try:
        print("Getting the latest Product list ...")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(PRODUCTS_URL, verify=False, timeout=10)  # noqa: S501
        csv_content = csv.DictReader(io.StringIO(response.text))
        for prod in csv_content:
            product = {
                "active": bool(int(prod["Active"])),
                "id": int(prod["ID"]),
                "name": prod["name"],
            }
            arch = prod["Architecture"]
            product["architectures"] = arch.split(",") if arch != "" else []
            products_list.append(product)
    except requests.exceptions.ConnectionError as error:
        error_message = (
            f"Failed to update with the latest Product list from {PRODUCTS_URL}"
            f" - error: {error}"
        )
        print(error_message)
        sys.exit(0)

    if products_list:
        with Path(prod_jsonfile).open("w") as json_file:
            products = {"products": products_list}
            json.dump(products, json_file, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Path to the products json file to generate")

    args = parser.parse_args()

    update_products_json(args.json_file)
