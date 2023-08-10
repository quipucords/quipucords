"""normalizer module."""

from logging import getLogger

logger = getLogger(__name__)


class NormalizerMeta(type):
    """
    Type for Normalizer classes.

    Customize class creation to provide the necessary magic for Normalizers.

    This metaclass is meant to be used ONLY on BaseNormalizer.
    """

    def __new__(cls, name, bases, attrs):
        """Blueprint for Normalizer classes."""
        # we need fields to be accessible as a class attribute. This is the WHOLE reason
        # for the existence of this metaclass (I wish python had a simpler api for this
        # type of thing).
        # Usually just creating a attribute on a base class would be enough
        # for this behavior, but not when you are dealing with dicts or lists.
        # (Creating 'fields' as a normal attribute on 'BaseNormalizer' class would
        # result on it being shared between the base class and its subclasses.)
        attrs["fields"] = {}
        return super().__new__(cls, name, bases, attrs)


class BaseNormalizer(metaclass=NormalizerMeta):
    """Base class for Normalizer classes."""

    # must be set for other implementations
    source_type = None

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
            fact_value, raw_fact_keys = self._normalize_fact(fact_name)
            self._normalized[fact_name] = fact_value
            self._metadata[fact_name] = {
                "raw_fact_keys": raw_fact_keys,
                "source_type": self.source_type,
                "server_id": self.server_id,
            }
        return self._normalized

    def _normalize_fact(self, fact_name):
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
            normalized_fact = field.normalizer_func(*args, **kwargs)
        except Exception:
            logger.exception("Unexpected error during '%s' normalization.", fact_name)
            return None, None
        try:
            for validator in field.validators:
                if not validator(normalized_fact):
                    logger.error(
                        "'{fact_name}' is invalid (value={normalized_fact})",
                        fact_name=fact_name,
                        normalized_fact=normalized_fact,
                    )
                    return None, None
        except Exception:
            logger.exception("Unexpected error during '%s' validation.", fact_name)
            return None, None
        # for now, assume all facts contributed
        return normalized_fact, field.raw_fact_keys


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
        self.fact_name = name
        # ensure dependencies are declared BEFORE this fact mapper
        for dep in self.dependencies:
            if dep not in normalizer.fields:
                raise ValueError(
                    f"'{dep}' can't be found on normalizer '{normalizer.__name__}'"
                )
        normalizer.fields[self.fact_name] = self
