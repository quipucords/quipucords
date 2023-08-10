"""test normalizer 'framework'."""

import json

import pytest

from scanner.normalizer import BaseNormalizer, FactMapper


def test_normalizer_creation():
    """Test creating a normalizer class without exploding anything."""

    class Normalizer(BaseNormalizer):
        fact1 = FactMapper("raw1", str)
        fact2 = FactMapper("raw2", str, dependencies=["fact1"])

    assert set(Normalizer.fields.keys()) == {"fact1", "fact2"}
    assert BaseNormalizer.fields == {}
    assert Normalizer.fact1.fact_name == "fact1"
    assert Normalizer.fact1.raw_fact_key == "raw1"
    assert Normalizer.fact1.dependencies == []
    assert Normalizer.fact2.fact_name == "fact2"
    assert Normalizer.fact2.raw_fact_key == "raw2"
    assert Normalizer.fact2.dependencies == ["fact1"]


def test_wrong_dependency_order():
    """Ensure that creating Normalizers with dependencies unordered will fail ASAP."""
    with pytest.raises(RuntimeError) as exc_info:

        class N(BaseNormalizer):
            fact1 = FactMapper("raw1", str, dependencies=["fact2"])
            fact2 = FactMapper("raw2", str)

    exc_cause = exc_info.value.__cause__
    assert isinstance(exc_cause, ValueError)
    assert str(exc_cause) == "'fact2' can't be found on normalizer 'N'"


def test_dependency(mocker):
    """Test normalization of facts with dependencies."""
    raw_facts = {"le_json": '{"final_answer": "42"}'}

    def _normalize_fact2(raw_fact, fact1):
        return int(fact1["final_answer"])

    class N(BaseNormalizer):
        fact1 = FactMapper("le_json", json.loads)
        fact2 = FactMapper(None, dependencies=["fact1"], normalizer=_normalize_fact2)

    norm = N(raw_facts, mocker.ANY)
    norm.normalize()
    assert norm.facts == {
        "fact1": {"final_answer": "42"},
        "fact2": 42,
    }
    # ensure data that would break a normalizer only affect one field
    norm2 = N({"le_json": '{"final_answer": "forty two"}'}, mocker.ANY)
    norm2.normalize()
    norm2.facts == {
        "fact1": {"final_answer": "forty two"},
        "fact2": None,
    }
