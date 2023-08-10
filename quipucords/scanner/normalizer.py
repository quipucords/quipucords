"""normalizer module."""

from logging import getLogger

from api.status.misc import get_server_id

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
        self.server_id = server_id or get_server_id()

    @property
    def facts(self):
        """Return normalized facts."""
        assert hasattr(
            self, "_normalized"
        ), "Call 'normalize()' before asking for facts."
        return self._normalized

    def normalize(self):
        """Normalize and validate raw facts.

        :return: dict of normalized facts
        """
        if hasattr(self, "_normalized"):
            return self._normalized
        self._normalized = {}
        for fact_name, field in self.fields.items():
            fact_value = self._normalize_fact(fact_name)
            self._metadata[fact_name] = {
                "raw_fact_key": field.raw_fact_key,
                "source_type": self.source_type,
                "server_id": self.server_id,
            }
            self._normalized[fact_name] = fact_value
        return self._normalized

    def _normalize_fact(self, fact_name):
        """
        Normalize given fact.

        Blind exceptions are used to ensure issues with normalization or validation
        functions don't affect other facts.
        """
        field = self.fields[fact_name]
        dep_kwargs = {dep: self._normalized[dep] for dep in field.dependencies}
        raw_value = self.raw_facts.get(field.raw_fact_key)
        try:
            normalized_fact = field.normalizer(raw_value, **dep_kwargs)
        except Exception:  # where's the blind exception error, ruff?
            logger.exception("Unexpected error during '%s' normalization.", fact_name)
            return None
        try:
            for validator in field.validators:
                if not validator(normalized_fact):
                    logger.error(
                        "'{fact_name}' is invalid (value={normalized_fact})",
                        fact_name=fact_name,
                        normalized_fact=normalized_fact,
                    )
                    return None
        except Exception:
            logger.exception("Unexpected error during '%s' validation.", fact_name)
            return None

        return normalized_fact


class FactMapper:
    """
    Utility for mapping raw facts to normalizers and validators.

    Must be used in conjunction with Normalizer classes.
    """

    def __init__(
        self,
        raw_fact_key: str,
        normalizer: callable,
        *,
        validators=None,
        dependencies: list[str] = None,
    ) -> None:
        """Instantiate FactMapper.

        :param raw_fact_key: name of the raw fact collected during inspection phase
        :param normalizer: function used to normalize raw fact (signature MUST be
            fn(raw_fact_value, **dependencies) where dependencies are kwargs from
            dependencies)
        :param validators: list of functions used to validate the output (signature
            fn(fact_value) -> bool)
        :param dependencies: list of normalized facts that this fact depends
        """
        self.raw_fact_key = raw_fact_key
        self.fact_name = None
        self.normalizer = normalizer
        self.dependencies = dependencies or []
        self.validators = validators or []

    def __set_name__(self, normalizer, name):
        """Configure FacMapper and Normalizer."""
        assert isinstance(
            normalizer, NormalizerMeta
        ), "FactMapper instances can only be bound to Normalizers"
        normalizer.fields[name] = self
        self.fact_name = name
        # ensure dependencies are declared BEFORE this fact mapper
        for dep in self.dependencies:
            if dep not in normalizer.fields:
                raise ValueError(
                    f"'{dep}' can't be found on normalizer '{normalizer.__name__}'"
                )
