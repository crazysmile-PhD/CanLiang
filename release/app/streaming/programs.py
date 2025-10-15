"""Program enumeration helpers built on top of ``WindowFinder``."""
from __future__ import annotations

from typing import List, Optional, Sequence

from .window_finder import WindowFinder


class ProgramLister:
    """Return de-duplicated window process names suitable for streaming."""

    def __init__(self, finder: Optional[WindowFinder] = None) -> None:
        self._finder = finder or WindowFinder()

    def list_programs(self, allowlist: Optional[Sequence[str]] = None) -> List[str]:
        programs = self._finder.list_visible_programs()
        if allowlist is None:
            return programs
        allowed = {name.lower() for name in allowlist}
        return [name for name in programs if name.lower() in allowed]

    def list_with_desktop(self, allowlist: Optional[Sequence[str]] = None, desktop_label: str = "桌面.exe") -> List[str]:
        programs = self.list_programs(allowlist)
        return programs + [desktop_label]
