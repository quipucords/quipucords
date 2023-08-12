"""normalizer module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import getLogger
from typing import Any

logger = getLogger(__name__)


class BaseNormalizer(ABC):
    """Base class for Normalizer classes."""

    @property
    @classmethod
    @abstractmethod
    def source_type() -> str:
        """Class attribute specifying which source type is used for this class."""

    # dict of normalized fact name to raw fact mappers.
    fields: dict = None

    def __init__(self, raw_facts: dict, server_id: str = None) -> None:
        """Create a normalizer instance.

        :param raw_facts: dict of raw facts from inspection phase
        :param server_id: server_id of quipucords server that collected these
        raw facts.
        """
        self.raw_facts = raw_facts
        self._metadata = {}
        self.server_id = server_id

    @property
    def facts(self):
        """Return normalized facts."""
        if not hasattr(self, "_normalized"):
            raise AssertionError(
                "You must call '.normalize()' before acessing `.facts`."
            )
        return self._normalized

    @property
    def metadata(self):
        """Return metadata for normalized facts."""
        if not hasattr(self, "_normalized"):
            raise AssertionError(
                "You must call '.normalize()' before acessing `.metadata`."
            )
        return self._metadata

    def normalize(self):
        """Normalize and validate raw facts.

        :return: dict of normalized facts
        """
        if hasattr(self, "_normalized"):
            return self._normalized
        self._normalized = {}
        for fact_name in self.fields.keys():
            norm_result = self._normalize_fact(fact_name)
            self._normalized[fact_name] = norm_result.value
            self._metadata[fact_name] = {
                "raw_fact_keys": norm_result.raw_fact_keys,
                "source_type": self.source_type,
                "server_id": self.server_id,
                "has_error": norm_result.has_error,
            }
        return self._normalized

    def _normalize_fact(self, fact_name) -> "NormalizedResult":
        """
        Normalize given fact.

        Blind exceptions are used to ensure issues with normalization or validation
        functions don't affect other facts.

        Returns the normalized fact and a list a raw facts used for normalization.
        """
        field: FactMapper = self.fields[fact_name]
        kwargs = {dep: self._normalized[dep] for dep in field.dependencies}
        if len(field.raw_fact_keys) == 1:
            raw_fact_key = field.raw_fact_keys[0]
            raw_value = self.raw_facts.get(raw_fact_key)
            args = (raw_value,)
        else:
            args = ()
            kwargs.update(
                **{raw: self.raw_facts.get(raw) for raw in field.raw_fact_keys}
            )
        try:
            norm_result = field.normalizer_func(*args, **kwargs)
        except Exception:
            logger.exception("Unexpected error during '%s' normalization.", fact_name)
            return NormalizedResult(None, has_error=True, raw_fact_keys=None)
        if not isinstance(norm_result, NormalizedResult):
            raw_fact_keys = self._get_raw_fact_keys(fact_name)
            norm_result = NormalizedResult(
                value=norm_result, raw_fact_keys=raw_fact_keys
            )
        else:
            self._check_raw_fact_keys_for_fact(fact_name, norm_result.raw_fact_keys)

        for validator in field.validators:
            try:
                is_valid = validator(norm_result.value)
            except Exception:
                logger.exception("Unexpected error during '%s' validation.", fact_name)
                return NormalizedResult(None, has_error=True, raw_fact_keys=None)
            if not is_valid:
                logger.error(
                    "'%s' is invalid (value={%s})", fact_name, norm_result.value
                )
                return NormalizedResult(None, has_error=True, raw_fact_keys=None)

        return norm_result

    @classmethod
    def _get_raw_fact_keys(cls, fact_name):
        field: FactMapper = cls.fields[fact_name]
        keys = set(field.raw_fact_keys)
        for dep in field.dependencies:
            dep_keys = cls.fields[dep].raw_fact_keys
            keys |= set(dep_keys)
        return sorted(keys)

    @classmethod
    def _check_raw_fact_keys_for_fact(cls, fact_name, raw_fact_keys):
        if not raw_fact_keys:
            return
        allowed_keys = set(cls._get_raw_fact_keys(fact_name))
        unexpected_keys = set(raw_fact_keys) - allowed_keys
        if unexpected_keys:
            raise AssertionError(
                f"Unexpected raw facts used for fact '{fact_name}': {unexpected_keys}",
            )


class FactMapper:
    """
    Utility for mapping raw facts to normalizers and validators.

    Must be used in conjunction with Normalizer classes.
    """

    def __init__(
        self,
        raw_fact_key: str | list[str] | None,
        normalizer_func: callable,
        *,
        validators=None,
        dependencies: list[str] = None,
    ) -> None:
        """Instantiate FactMapper.

        :param raw_fact_key: raw fact name or list of raw fact names used to normalize a
            fact
        :param normalizer_func: function used to normalize raw fact. When raw_fact_key
            is a str, signature of normalizer SHOULD be `fn(raw_fact_value, **kwargs)`
            where kwargs are dependencies. When raw_fact_key is a list, signature should
            be `fn(**kwargs)`, where kwargs are raw facts and dependencies.
        :param validators: list of functions used to validate the output (signature
            fn(fact_value) -> bool)
        :param dependencies: list of normalized facts that this fact depends
        """
        if isinstance(raw_fact_key, str):
            self.raw_fact_keys = [raw_fact_key]
        elif raw_fact_key is None:
            self.raw_fact_keys = []
        else:
            self.raw_fact_keys = raw_fact_key
        self.fact_name = None
        self.normalizer_func = normalizer_func
        self.dependencies = dependencies or []
        self.validators = validators or []

    def __set_name__(self, normalizer, name):
        """Configure FacMapper and Normalizer."""
        if not issubclass(normalizer, BaseNormalizer):
            raise AssertionError(
                "FactMapper instances can only be bound to Normalizers"
            )
        if normalizer.fields is None:
            # concrete normalizer classes require class attribute 'fields' to map
            # fact_name to FactMappers in the exact order they were created (see
            # normalize method on BaseNormalizer and the method
            # `_ensure_dependencies_exist` below).
            # 'fields' dict can't be created at BaseNormalizer level otherwise all
            # implementations will share it. Can't be done at normalizer instance level
            # either because this method don't have access to it (we are dealing with
            # class construction here).
            # As odd as it seems to create something for another class here, given the
            # symbiotic relationship between Normalizers and FactMappers, this seems to
            # be the sweetspot for it and a good trade off.
            normalizer.fields = {}
        # ensure dependencies are created BEFORE this one
        self._ensure_dependencies_exist(normalizer)
        normalizer.fields[name] = self
        self.fact_name = name

    def _ensure_dependencies_exist(self, normalizer):
        for dep in self.dependencies:
            if dep not in normalizer.fields:
                raise ValueError(
                    f"'{dep}' can't be found on normalizer '{normalizer.__name__}'"
                )


@dataclass
class NormalizedResult:
    """
    Wrapper for normalized fact value.

    Contains the actual value with extra metadata.
    """

    value: Any
    raw_fact_keys: list
    has_error: bool = False


def str_or_none(value):
    """Normalize value to be a string (or None when "empty")."""
    if not value:
        return None
    return str(value)
