import argparse

import pytest

from loadtest.cli import load_json_body, parse_header


def test_parse_header_splits_only_first_colon() -> None:
    assert parse_header("Authorization: Bearer value:part") == (
        "Authorization",
        "Bearer value:part",
    )


def test_parse_header_rejects_invalid_value() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_header("missing-separator")


def test_load_json_body_reads_inline_json() -> None:
    assert load_json_body('{"name": "Maria"}', None) == {"name": "Maria"}
