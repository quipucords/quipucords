"""Build rpm-lockfile-prototype container."""

import logging
import subprocess
from datetime import datetime, timedelta, timezone
from io import StringIO

import click
import requests
from podman import PodmanClient
from podman.errors.exceptions import ImageNotFound

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_latest_image_digest(image: str) -> str:
    """Get the latest digest of the specified image."""
    command = f"skopeo inspect --raw 'docker://{image}:latest' | sha256sum"
    try:
        latest_digest = (
            subprocess.check_output(command, shell=True)  # noqa: S602
            .decode("utf-8")
            .split()[0]
            .strip()
        )
        logger.info("Latest digest for %s: %s", image, latest_digest)
        return latest_digest
    except subprocess.CalledProcessError as e:
        logger.error("Failed to get latest digest for %s: %s", image, e)
        raise


def download_containerfile(url: str) -> str:
    """Download the Containerfile from the specified URL."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        logger.info("Downloaded Containerfile from %s", url)
        return response.text
    except requests.RequestException as e:
        logger.error("Failed to download Containerfile: %s", e)
        raise


def image_needs_building(
    client: PodmanClient, image_name: str, age_threshold: timedelta
) -> bool:
    """Check if the image needs to be built based on its age."""
    try:
        image = client.images.get(image_name)
    except ImageNotFound:
        logger.info("Image %s not found. It needs to be built.", image_name)
        return True

    creation_time = datetime.fromisoformat(image.attrs["Created"])
    if datetime.now(timezone.utc) - creation_time > age_threshold:
        logger.info(
            "Image %s is older than %s. It needs to be rebuilt.",
            image_name,
            age_threshold,
        )
        return True

    logger.info("Image %s is up to date.", image_name)
    return False


def build_image(
    client: PodmanClient,
    image_name: str,
    base_image: str,
    latest_digest: str,
    containerfile_content: str,
):
    """Build the image using the provided Containerfile content."""
    build_args = {"BASE_IMAGE": f"{base_image}@sha256:{latest_digest}"}
    with StringIO(containerfile_content) as file_obj:
        client.images.build(
            fileobj=file_obj,
            tag=image_name,
            buildargs=build_args,
        )
    logger.info("Image %s built successfully.", image_name)


@click.command()
@click.option(
    "--image-name",
    default="localhost/rpm-lockfile-prototype",
    help="Name of the image to build.",
)
@click.option(
    "--base-image",
    default="registry.access.redhat.com/ubi9",
    help="Base image to use for building.",
)
@click.option(
    "--age-threshold",
    default=36,
    type=int,
    help="Age threshold in hours for the image to be rebuilt.",
)
def main(image_name: str, base_image: str, age_threshold: int):
    """Check and build the image if necessary."""
    age_threshold_timedelta = timedelta(hours=age_threshold)
    containerfile_url = "https://raw.githubusercontent.com/konflux-ci/rpm-lockfile-prototype/refs/heads/main/Containerfile"

    with PodmanClient() as client:
        if image_needs_building(client, image_name, age_threshold_timedelta):
            latest_digest = get_latest_image_digest(base_image)
            containerfile_content = download_containerfile(containerfile_url)
            logger.info("Building image %s...", image_name)
            build_image(
                client, image_name, base_image, latest_digest, containerfile_content
            )
        else:
            logger.info("Image %s already exists and is up to date.", image_name)


if __name__ == "__main__":
    main()
