"""Tests for the required-document checklist single source of truth."""
from agents.config.required_documents import (
    get_required_documents,
    BASE_REQUIRED_DOCUMENTS,
)


def test_base_requirements_returned_by_default():
    docs = get_required_documents()
    keys = {d["key"] for d in docs}
    assert keys == {d["key"] for d in BASE_REQUIRED_DOCUMENTS}
    assert len(docs) == len(BASE_REQUIRED_DOCUMENTS)


def test_finance_adds_audited_financials():
    keys = [d["key"] for d in get_required_documents(business_type="Finance")]
    assert "audited_financials" in keys


def test_manufacturing_adds_insurance():
    keys = [d["key"] for d in get_required_documents(business_type="Manufacturing")]
    assert "insurance_certificate" in keys


def test_eu_country_adds_gdpr():
    keys = [d["key"] for d in get_required_documents(country="Germany")]
    assert "gdpr_data_processing_agreement" in keys


def test_non_eu_country_has_no_gdpr():
    keys = [d["key"] for d in get_required_documents(country="India")]
    assert "gdpr_data_processing_agreement" not in keys


def test_results_are_deduplicated_by_key():
    keys = [d["key"] for d in get_required_documents("Finance", "Germany")]
    assert len(keys) == len(set(keys))


def test_each_entry_has_required_fields():
    for d in get_required_documents("Manufacturing", "France"):
        assert {"key", "label", "keywords"} <= set(d.keys())
