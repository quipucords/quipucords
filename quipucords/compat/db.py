"""db compatibility module."""

from django.contrib.postgres.aggregates import StringAgg as PostgresStringAgg
from django.db import connection
from django.db.models import Aggregate, CharField


class SQLiteStringAgg(Aggregate):
    """StringAgg for sqlite based on GROUP_CONCAT function.

    Aims to be compatible with StringAgg for postgres.

    https://www.sqlite.org/lang_aggfunc.html
    """

    function = "GROUP_CONCAT"
    template = "%(function)s(%(expressions)s,%(delimiter)s)"

    def __init__(self, expressions, delimiter=",", **extra):
        """Initialize aggregator."""
        self.default_value = self._get_default_value(extra)
        super().__init__(
            expressions,
            delimiter=f'"{delimiter}"',
            output_field=CharField(),
            **extra,
        )

    def convert_value(self, value, expression, connection):
        """Convert NULL value to default_value."""
        # arguments-differ is a false positive here - see how django sql compiler
        # handles this https://github.com/django/django/blob/f6f0699d01f5840437bfd236c76c797943ef8edc/django/db/models/sql/compiler.py#L1105-L1124 # noqa: E501
        # other checks were disable to respect the expected signature of this function
        if value is None:
            return self.default_value
        return value

    def _get_default_value(self, extra):
        default = extra.pop("default")
        if default is not None:
            try:
                # assuming this is an instance of django.db.models.Value
                return default.value
            except AttributeError:
                # ok then... it's not ¯\_(ツ)_/¯
                return default
        return None


class StringAgg:
    """Proxy for the appropriate StringAgg based on current db connection."""

    def __new__(cls, expressions, delimiter=",", **extra):
        """Initialize the proper StringAgg."""
        if connection.vendor == "postgresql":
            string_agg_cls = PostgresStringAgg
        elif connection.vendor == "sqlite":
            string_agg_cls = SQLiteStringAgg
        else:
            raise NotImplementedError(
                f"StringAgg not implemented for {connection.vendor=}"
            )
        return string_agg_cls(expressions, delimiter, **extra)
