"""Filters feature flags from system env variables."""

import os

DEFAULT_FEATURE_FLAGS_VALUES = {"OVERALL_STATUS": True, "UPTIME": True}

VALID_VALUES_FOR_ENV_VARIABLES = ["0", "1"]


class FeatureFlag:
    """Handle environment variables and its status."""

    def __init__(self):
        """Attributes and values are generated dynamically.

        Attributes keys-values are received in initial_data.
        """
        initial_data = self.get_feature_flags_from_env()
        self._feature_flags = initial_data

    def __getattr__(self, item):
        """Look for attribute in self._feature_flags."""
        try:
            return self._feature_flags[item]
        except KeyError:
            return super().__getattribute__(item)

    def is_feature_active(self, feature_name):
        """Return attribute value."""
        try:
            return getattr(self, feature_name)
        except AttributeError as exception:
            raise ValueError(f"{feature_name=} is not a valid input.") from exception

    @classmethod
    def get_feature_flags_from_env(cls):
        """Filter feature flags from environment variables."""
        feature_flags = DEFAULT_FEATURE_FLAGS_VALUES.copy()
        for key, value in os.environ.items():
            if key.upper().startswith("QPC_FEATURE_"):
                feature_name = key.upper().replace("QPC_FEATURE_", "")
                feature_value = value.strip()
                if feature_value in VALID_VALUES_FOR_ENV_VARIABLES:
                    feature_flags[feature_name] = bool(int(feature_value))
                else:
                    raise ValueError(
                        f"'{feature_value}' from '{key}' can't be converted "
                        "to int, verify your environment variables."
                    )
        return feature_flags

    def as_dict(self):
        """Return all feature flags in dict format."""
        return self._feature_flags
