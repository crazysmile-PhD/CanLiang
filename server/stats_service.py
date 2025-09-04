import json
from datetime import datetime, timedelta
from pathlib import Path


class StatsService:
    """Service for reading stats from a directory of JSONL files."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def _date_range(self, start_date, end_date):
        current = start_date
        while current <= end_date:
            yield current
            current += timedelta(days=1)

    def load_range(self, start_date, end_date):
        """Load JSON lines within the given inclusive date range.

        Args:
            start_date (date): starting date (inclusive)
            end_date (date): ending date (inclusive)

        Returns:
            list: list of dict objects loaded from files.
        """
        data = []
        for d in self._date_range(start_date, end_date):
            file_path = self.data_dir / f"{d.strftime('%Y-%m-%d')}.jsonl"
            if not file_path.exists():
                continue
            with file_path.open('r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data.append(json.loads(line))
        return data
