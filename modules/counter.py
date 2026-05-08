# Request counter — daily sequence number from today's log file
import os
import re
from datetime import datetime
from pathlib import Path


class RequestCounter:
    def __init__(self, log_dir: Path):
        today = datetime.now().strftime("%Y%m%d")
        self._logfile = log_dir / f"{today}.log"
        self.request  = self._load_last() + 1

    def _load_last(self) -> int:
        if not self._logfile.exists():
            return 0
        with self._logfile.open("rb") as f:
            try:
                f.seek(-4096, os.SEEK_END)
            except OSError:
                f.seek(0)
            lines = f.read().decode(errors="ignore").splitlines()
        for line in reversed(lines):
            m = re.search(r"request:\s*(\d+)", line)
            if m:
                return int(m.group(1))
        return 0
