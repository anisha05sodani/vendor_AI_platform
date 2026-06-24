"""Tests for the robust JSON-extraction helper used to parse LLM output."""
import json

import pytest

from agents.utils.llm import extract_json


def test_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_fenced_json_with_lang():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_fenced_json_without_lang():
    assert extract_json('```\n{"a": 1}\n```') == {"a": 1}


def test_prose_preamble():
    assert extract_json('Here is the JSON:\n{"a": 1}') == {"a": 1}


def test_trailing_prose():
    assert extract_json('Sure! {"b": 2} hope that helps') == {"b": 2}


def test_nested_object():
    assert extract_json('{"a": {"b": [1, 2, 3]}}') == {"a": {"b": [1, 2, 3]}}


def test_empty_string_raises():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        extract_json("")


def test_no_json_raises():
    with pytest.raises((ValueError, json.JSONDecodeError)):
        extract_json("no json content here at all")
