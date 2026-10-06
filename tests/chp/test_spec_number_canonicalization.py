"""Spec §3.1 number rendering (RFC 8785) — the cross-language hash gap (D-B1)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spec" / "conformance"))
import chp_reference as ref  # noqa: E402


@pytest.mark.parametrize("value,expected", [
    (100.0, "100"), (100, "100"), (0.55, "0.55"), (-0.0, "0"),
    (1e21, "1e+21"), (1e20, "100000000000000000000"),
    (1e-7, "1e-7"), (1e-6, "0.000001"), (0.1 + 0.2, "0.30000000000000004"),
    (5e-324, "5e-324"), (-12345.678, "-12345.678"),
])
def test_number_rendering(value, expected):
    assert ref.canonical_json({"x": value}) == '{"x":%s}' % expected


def test_float_and_int_hash_identically():
    assert ref.content_hash({"notional": 100.0}) == ref.content_hash({"notional": 100})


def test_unsafe_integer_rejected():
    with pytest.raises(ValueError):
        ref.canonical_json({"x": 2**53})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_rejected(bad):
    with pytest.raises(ValueError):
        ref.canonical_json({"x": bad})


def test_keys_sort_by_utf16_not_code_point():
    # U+10000 is surrogate D800 in UTF-16, so it sorts BEFORE U+FFFF.
    assert ref.canonical_json({"￿": 1, "\U00010000": 2}) == '{"\U00010000":2,"￿":1}'
