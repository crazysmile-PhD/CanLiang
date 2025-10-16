"""Preview mode definitions and helpers shared across the API layer."""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class PreviewMode(str, Enum):
    """Supported preview modes for runtime streaming."""

    NONE = "none"
    SUNSHINE = "sunshine"
    WEB_RTC = "web-rtc"
    LL_HLS = "ll-hls"

    @classmethod
    def choices(cls) -> list[str]:
        """Return the list of string choices for CLI and validators."""

        return [mode.value for mode in cls]


DEFAULT_PREVIEW_MODE = PreviewMode.NONE.value
BROWSER_STREAMING_MODES = {PreviewMode.WEB_RTC.value, PreviewMode.LL_HLS.value}
EXTERNAL_CLIENT_MODES = {PreviewMode.SUNSHINE.value}
SUPPORTED_PREVIEW_MODES = frozenset(PreviewMode.choices())


class PreviewModeError(RuntimeError):
    """Raised when the requested preview mode does not support browser streaming."""

    def __init__(self, message: str, *, preview_mode: str):
        super().__init__(message)
        self.preview_mode = preview_mode


def normalize_preview_mode(mode: str) -> str:
    """Return a canonical preview mode or raise ``ValueError`` for unknown values."""

    if mode not in SUPPORTED_PREVIEW_MODES:
        raise ValueError(f"不支持的预览模式: {mode}")
    return mode


def preview_mode_supports_browser(mode: str) -> bool:
    """Return True when ``mode`` is usable by the built-in MJPEG preview."""

    return normalize_preview_mode(mode) in BROWSER_STREAMING_MODES


def preview_mode_requires_external_client(mode: str) -> bool:
    """Return True when ``mode`` requires Sunshine or another external client."""

    return normalize_preview_mode(mode) in EXTERNAL_CLIENT_MODES


def preview_mode_is_disabled(mode: str) -> bool:
    """Return True when previewing is explicitly disabled."""

    return normalize_preview_mode(mode) == PreviewMode.NONE.value


def ensure_browser_capable_mode(mode: str, *, allow: Iterable[str] | None = None) -> str:
    """Validate a preview mode for MJPEG streaming and return its canonical value."""

    canonical = normalize_preview_mode(mode)
    allow_set = set(allow) if allow is not None else BROWSER_STREAMING_MODES
    if canonical not in allow_set:
        raise PreviewModeError(
            f"不支持的预览模式: {canonical}",
            preview_mode=canonical,
        )
    return canonical
