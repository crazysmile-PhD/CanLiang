import pytest

from app.infrastructure import utils


def test_parse_timestamp_to_seconds_handles_milliseconds():
    assert utils.parse_timestamp_to_seconds('04:10:02.395') == pytest.approx(4 * 3600 + 10 * 60 + 2.395)


def test_parse_timestamp_to_seconds_handles_seconds_only():
    assert utils.parse_timestamp_to_seconds('12:30:45') == 12 * 3600 + 30 * 60 + 45


def test_check_dict_empty_validates_structure():
    assert utils.check_dict_empty({'a': [], 'b': []}) is True
    assert utils.check_dict_empty({'a': [1], 'b': [2]}) is False

    with pytest.raises(Exception):
        utils.check_dict_empty({'a': [1], 'b': [1, 2]})
