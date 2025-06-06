"""Util for common report operations."""

import io
import logging
import tarfile

from rest_framework.renderers import JSONRenderer

from quipucords.environment import server_version

logger = logging.getLogger(__name__)


REPORT_TYPE_DETAILS = "details"
REPORT_TYPE_DEPLOYMENT = "deployments"
REPORT_TYPE_CHOICES = (
    (REPORT_TYPE_DETAILS, REPORT_TYPE_DETAILS),
    (REPORT_TYPE_DEPLOYMENT, REPORT_TYPE_DEPLOYMENT),
)


def create_report_version():
    """Create the report version string."""
    return server_version()


def sanitize_row(row):
    """Replace commas in fact values to prevent false csv parsing."""
    new_row = [
        fact.replace(",", ";") if isinstance(fact, str) else fact for fact in row
    ]
    new_row = [
        fact.replace("\r", ";") if isinstance(fact, str) else fact for fact in new_row
    ]
    new_row = [
        fact.replace("\n", ";") if isinstance(fact, str) else fact for fact in new_row
    ]
    return new_row


def create_filename(file_name, file_ext, report_id, detailed_filename=False):
    """Create the filename."""
    file_name = f"report_id_{report_id}/{file_name}"
    if detailed_filename:
        file_name += f"-{report_id}"
    if file_ext:
        file_name += f".{file_ext}"
    return file_name


def encode_content(content, file_format):
    """Encode content as bytes based on its file format."""

    def _textfile_encoder(content):
        return content.encode("utf-8")

    renderer = {
        "json": JSONRenderer().render,
        "csv": _textfile_encoder,
        "plaintext": _textfile_encoder,
    }
    return renderer[file_format](content)


def create_tar_buffer(files_data) -> io.BytesIO | None:
    """Generate a file buffer based off a dictionary.

    :param files_data: A dictionary of strings.
        :key: filepath with filename included
        :value: the contents of the file encoded as bytes
    """
    if not isinstance(files_data, dict):
        return None
    if not all(isinstance(v, bytes) for v in files_data.values()):
        return None
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar_file:
        for file_name, file_content in files_data.items():
            file_buffer = io.BytesIO(file_content)
            info = tarfile.TarInfo(name=file_name)
            info.size = len(file_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=file_buffer)
    tar_buffer.seek(0)
    return tar_buffer


class CSVHelper:
    """Helper for CSV serialization of list/dict values."""

    ANSIBLE_ERROR_MESSAGE = "Error. See logs."

    def serialize_value(self, header, fact_value):
        """Serialize a fact value to a CSV value."""
        if isinstance(fact_value, dict):
            return self.serialize_dict(header, fact_value)
        elif isinstance(fact_value, list):
            return self.serialize_list(header, fact_value)
        return fact_value

    def serialize_list(self, header, fact_list):
        """Serialize a list to a CSV value."""
        # Return empty string for empty list
        if not bool(fact_list):
            return ""

        result = "["
        value_string = "%s;"
        for item in fact_list:
            if isinstance(item, list):
                result += value_string % self.serialize_list(header, item)
            elif isinstance(item, dict):
                result += value_string % self.serialize_dict(header, item)
            else:
                result += value_string % item
        result = result[:-1] + "]"
        return result

    def serialize_dict(self, header, fact_dict):
        """Serialize a dict to a CSV value."""
        # Return empty string for empty dict
        if not bool(fact_dict):
            return ""
        if fact_dict.get("rc") is not None:
            logger.error(
                "Fact appears to be raw ansible output. %s=%s", header, fact_dict
            )
            return self.ANSIBLE_ERROR_MESSAGE

        result = "{"
        value_string = "%s:%s;"
        for key, value in fact_dict.items():
            if isinstance(value, list):
                result += value_string % (key, self.serialize_list(header, value))
            elif isinstance(value, dict):
                result += value_string % (key, self.serialize_dict(header, value))
            else:
                result += value_string % (key, value)
        result = result[:-1] + "}"
        return result

    @staticmethod
    def generate_headers(fact_list, exclude=None):
        """Generate column headers from fact list."""
        headers = set()
        for fact in fact_list:
            fact_addon = {}
            for fact_key in fact.keys():
                if fact_key == "products":
                    prods = fact.get(fact_key, [])
                    if prods:
                        for prod in prods:
                            prod_name = prod.get("name")
                            if prod_name:
                                prod_name = prod_name.lower()
                                headers.add(prod_name)
                                fact_addon[prod_name] = prod.get("presence", "unknown")
                else:
                    headers.add(fact_key)
            fact.update(fact_addon)

        if exclude and isinstance(exclude, set):
            headers = headers - exclude
        return sorted(list(headers))
