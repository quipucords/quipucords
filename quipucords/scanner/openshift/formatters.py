# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Fingerprint formatters for OpenShift."""

from collections import defaultdict
from itertools import product


def _strip_hash_or_version(image_name):
    return image_name.split("@")[0].split(":")[0]


def image_names(deployment_list) -> list:
    """Return a deduplicated list of all image names from given deployments."""
    images_set = set()
    for image_list_key, deployment_dict in product(
        ["container_images", "init_container_images"], deployment_list
    ):
        for image_name in deployment_dict[image_list_key]:
            images_set.add(_strip_hash_or_version(image_name))
    return sorted(images_set)


def labels(deployment_list) -> dict:
    """Group labels from the same key for a given deployment list."""
    labels_dict = defaultdict(set)
    for deployment_dict in deployment_list:
        for label_key, label_value in deployment_dict["labels"].items():
            labels_dict[label_key].add(label_value)
    return {k: sorted(v) for k, v in labels_dict.items()}
