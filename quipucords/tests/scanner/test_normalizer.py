"""test normalizer 'framework'."""

import json
import logging
import sys

import pytest

from scanner.normalizer import BaseNormalizer, FactMapper, NormalizedResult

is_python_3_12_or_above = sys.version_info >= (3, 12, 0)


def test_normalizer_creation():
    """Test creating a normalizer class without exploding anything."""

    class Normalizer(BaseNormalizer):
        fact1 = FactMapper("raw1", str)
        fact2 = FactMapper("raw2", str, dependencies=["fact1"])

    assert set(Normalizer.fields.keys()) == {"fact1", "fact2"}
    assert BaseNormalizer.fields is None
    assert Normalizer.fact1.fact_name == "fact1"
    assert Normalizer.fact1.raw_fact_keys == ["raw1"]
    assert Normalizer.fact1.dependencies == []
    assert Normalizer.fact2.fact_name == "fact2"
    assert Normalizer.fact2.raw_fact_keys == ["raw2"]
    assert Normalizer.fact2.dependencies == ["fact1"]


def test_wrong_dependency_order():
    """Ensure that creating Normalizers with dependencies unordered will fail ASAP."""
    expected_exception_type = ValueError if is_python_3_12_or_above else RuntimeError

    with pytest.raises(expected_exception_type) as exc_info:

        class N(BaseNormalizer):
            fact1 = FactMapper("raw1", str, dependencies=["fact2"])
            fact2 = FactMapper("raw2", str)

    exc_cause = exc_info.value if is_python_3_12_or_above else exc_info.value.__cause__
    assert isinstance(exc_cause, ValueError)
    assert str(exc_cause) == "'fact2' can't be found on normalizer 'N'"


@pytest.mark.parametrize(
    "raw_facts, expected_value, expected_raw_facts, expected_has_error",
    [
        ({"raw": "0"}, None, None, True),
        ({"raw": "1"}, None, None, True),
        ({"raw": "2"}, 2, ["raw"], False),
    ],
)
def test_validators(
    raw_facts, expected_value, expected_raw_facts, expected_has_error, faker
):
    """Ensure validators are used (if provided)."""

    def _is_even(num):
        return num % 2 == 0

    def _not_zero(num):
        # throw an error when zero to cover exceptions by validators
        if num == 0:
            raise ValueError()
        return True

    class N(BaseNormalizer):
        source_type = faker.slug()
        even_fact = FactMapper("raw", int, validators=[_is_even, _not_zero])

    norm = N(raw_facts=raw_facts, server_id=faker.uuid4())
    norm.normalize()
    assert norm.facts["even_fact"] == expected_value
    assert norm.metadata["even_fact"]["has_error"] == expected_has_error
    assert norm.metadata["even_fact"]["raw_fact_keys"] == expected_raw_facts


def test_dependency(faker):
    """Test normalization of facts with dependencies."""
    raw_facts = {"le_json": '{"final_answer": "42"}'}

    def _normalize_fact2(*, fact1):
        return int(fact1["final_answer"])

    class N(BaseNormalizer):
        source_type = faker.slug()

        fact1 = FactMapper("le_json", json.loads)
        fact2 = FactMapper(
            None, dependencies=["fact1"], normalizer_func=_normalize_fact2
        )

    server_id = faker.uuid4()
    norm = N(raw_facts, server_id)
    norm.normalize()
    assert norm.facts == {
        "fact1": {"final_answer": "42"},
        "fact2": 42,
    }
    assert norm.metadata == {
        "fact1": {
            "has_error": False,
            "raw_fact_keys": ["le_json"],
            "server_id": server_id,
            "source_type": N.source_type,
        },
        "fact2": {
            "has_error": False,
            "raw_fact_keys": ["le_json"],
            "server_id": server_id,
            "source_type": N.source_type,
        },
    }
    # ensure data that would break a normalizer only affect one field
    server_id2 = faker.uuid4()
    norm2 = N({"le_json": '{"final_answer": "forty two"}'}, server_id2)
    norm2.normalize()
    assert norm2.facts == {
        "fact1": {"final_answer": "forty two"},
        "fact2": None,
    }
    assert norm2.metadata == {
        "fact1": {
            "has_error": False,
            "raw_fact_keys": ["le_json"],
            "server_id": server_id2,
            "source_type": N.source_type,
        },
        "fact2": {
            "has_error": True,
            "raw_fact_keys": None,
            "server_id": server_id2,
            "source_type": N.source_type,
        },
    }


class TestMultipleRawFacts:
    """Test support for normalizers using multiple raw fact keys."""

    @staticmethod
    def _normalizer_simple(*, raw1, raw2):
        return raw1 + raw2

    @staticmethod
    def _normalizer_custom_result(*, raw1, raw2):
        value = raw1 + raw2
        return NormalizedResult(value=value, raw_fact_keys=["raw1", "raw2"])

    @staticmethod
    def _normalizer_unknown_raw_fact(*, raw1, raw2):
        value = raw1 + raw2
        return NormalizedResult(value=value, raw_fact_keys=["raw3"])

    @pytest.mark.parametrize(
        "normalizer",
        [
            _normalizer_simple,
            _normalizer_custom_result,
        ],
    )
    def test_multiple_raw_facts(self, mocker, normalizer):
        """Test normalization of facts that depend on multiple raw facts directly."""
        raw_facts = {"raw1": 2, "raw2": 3}

        class N(BaseNormalizer):
            source_type = mocker.ANY
            fact = FactMapper(["raw1", "raw2"], normalizer)

        norm = N(raw_facts, mocker.ANY)
        norm.normalize()
        assert norm.facts == {"fact": 5}

    def test_normalizer_with_unknown_raw_fact_key(self, mocker, caplog):
        """Test a normalizer that says it depends on unexpected keys."""
        raw_facts = {"raw1": 2, "raw2": 3}
        caplog.set_level(logging.ERROR)

        class N(BaseNormalizer):
            source_type = mocker.ANY
            fact = FactMapper(["raw1", "raw2"], self._normalizer_unknown_raw_fact)

        norm = N(raw_facts, mocker.ANY)
        with pytest.raises(
            AssertionError, match="Unexpected raw facts used for fact 'fact': {'raw3'}"
        ):
            norm.normalize()


class TestMultipleNormalizers:
    """Test interaction between multiple normalizers."""

    def test_distinct_fact_names(self):
        """Ensure one normalizer class does not leak info to another."""
        assert BaseNormalizer.fields is None

        class N1(BaseNormalizer):
            fact1 = FactMapper("some_raw_fact", str)

        class N2(BaseNormalizer):
            fact2 = FactMapper("another_raw_fact", str)

        assert BaseNormalizer.fields is None
        assert N1.fields == {"fact1": N1.fact1}
        assert N2.fields == {"fact2": N2.fact2}

    def test_same_fact_name(self):
        """Ensure one normalizer class does not leak info to another."""
        assert BaseNormalizer.fields is None

        class N1(BaseNormalizer):
            fact1 = FactMapper("foo", str)

        class N2(BaseNormalizer):
            fact1 = FactMapper("bar", str)

        assert N1.fact1 != N2.fact1
        assert BaseNormalizer.fields is None
        assert N1.fields == {"fact1": N1.fact1}
        assert N2.fields == {"fact1": N2.fact1}

    def test_indirect_inheritance(self):
        """Ensure Normalizers fields can behave properly when built with inheritance."""

        class Parent(BaseNormalizer):
            common_fact = FactMapper("some_fact", str)

        class Child1(Parent):
            fact1 = FactMapper("foo", str)

        class Child2(Parent):
            fact2 = FactMapper("bar", str)

        assert Parent.fields == {"common_fact": Parent.common_fact}
        assert Child1.fields == {
            "fact1": Child1.fact1,
            "common_fact": Child1.common_fact,
        }
        assert Child2.fields == {
            "fact2": Child2.fact2,
            "common_fact": Child2.common_fact,
        }

    def test_depending_on_another_class(self):
        """Ensure a normalizer fact cant depend on another class fact."""

        class N1(BaseNormalizer):
            fact1 = FactMapper("raw1", str)

        expected_exception_type = (
            ValueError if is_python_3_12_or_above else RuntimeError
        )
        with pytest.raises(expected_exception_type) as exc_info:

            class N2(BaseNormalizer):
                fact2 = FactMapper("raw2", str, dependencies=["fact1"])

        exc_cause = (
            exc_info.value if is_python_3_12_or_above else exc_info.value.__cause__
        )
        assert isinstance(exc_cause, ValueError)
        assert str(exc_cause) == "'fact1' can't be found on normalizer 'N2'"
