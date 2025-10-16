import pytest

from app.api import preview


def test_normalize_preview_mode_returns_canonical_value():
    assert preview.normalize_preview_mode("web-rtc") == "web-rtc"


def test_normalize_preview_mode_rejects_unknown_value():
    with pytest.raises(ValueError):
        preview.normalize_preview_mode("invalid")


def test_preview_mode_helpers_cover_expected_categories():
    assert preview.preview_mode_is_disabled("none") is True
    assert preview.preview_mode_requires_external_client("sunshine") is True
    assert preview.preview_mode_supports_browser("web-rtc") is True
    assert preview.preview_mode_supports_browser("ll-hls") is True


def test_ensure_browser_capable_mode_rejects_non_browser_modes():
    with pytest.raises(preview.PreviewModeError) as exc:
        preview.ensure_browser_capable_mode("sunshine")
    assert exc.value.preview_mode == "sunshine"
