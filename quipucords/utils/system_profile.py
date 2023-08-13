"""system_profile validator."""

from functools import cache, partial

import jsonschema
import referencing
import yaml
from django.conf import settings

URI = "urn:system-profile"


@cache
def _system_profile():
    _schema_path = settings.BASE_DIR.parent / "schemas/system_profile/schema.yaml"
    _schema = yaml.safe_load(_schema_path.read_text())
    registry = referencing.Registry()
    resource = referencing.Resource(
        contents=_schema, specification=referencing.jsonschema.DRAFT4
    )
    return registry.with_resource(uri=URI, resource=resource)


class SystemProfile:
    """Misc helpers for system profile."""

    @classmethod
    def is_fact(self, fact_name):
        """Return true if fact_name belongs to system_profile."""
        facts = set(
            _system_profile()
            .resolver()
            .lookup(f"{URI}#/$defs/SystemProfile/properties")
            .contents.keys()
        )
        return fact_name in facts

    @classmethod
    def validate_field(cls, value, field_name):
        """Validate an specific system profile property."""
        field_schema = (
            _system_profile()
            .resolver()
            .lookup(f"{URI}#/$defs/SystemProfile/properties/{field_name}")
            .contents
        )
        # required for $ref resolution
        field_schema["$defs"] = (
            _system_profile().resolver().lookup(f"{URI}#/$defs").contents
        )
        # jsonschema.validate returns None - it raises exceptions on validation failures
        jsonschema.validate(
            value, schema=field_schema, cls=jsonschema.validators.Draft4Validator
        )
        return True

    @classmethod
    def validator_factory(cls, field_name):
        """Return a validator function for field_name."""
        return partial(cls.validate_field, field_name=field_name)
