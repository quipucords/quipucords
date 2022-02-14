import os
import logging

DEFAULT_FEATURE_FLAGS_VALUES = {
    'OVERALL_STATUS': False}  # default values for feature flags that are already implemented
VALID_VALUES_FOR_ENV_VARIABLES = ["0", "1"]

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_feature_flags_from_env():
    """Filters feature flags from environment variables"""

    global DEFAULT_FEATURE_FLAGS_VALUES
    global VALID_VALUES_FOR_ENV_VARIABLES
    for key, value in os.environ.items():
        if key.upper().startswith("QPC_FEATURE_"):
            feature = key.upper().replace("QPC_FEATURE_", "")
            try:
                if value in VALID_VALUES_FOR_ENV_VARIABLES:
                    DEFAULT_FEATURE_FLAGS_VALUES[feature] = bool(int(value))
            except ValueError:
                logger.info(f"{value} can`t be converted to int, verify your environment variables.")
                continue
    return DEFAULT_FEATURE_FLAGS_VALUES


class FeatureFlag:

    def __init__(self, initial_data):
        for key, value in initial_data.items():
            setattr(self, key, value)

    def is_feature_active(self, feature_name):
        try:
            return getattr(self, feature_name)
        except AttributeError:
            raise ValueError(f"{feature_name=} is not a valid input.")
