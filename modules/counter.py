# Request counter — daily sequence number from log file
import os
import re
from datetime import datetime


class RequestCounter:
    def __init__(self, logfile: str = "ai.log"):
        self.logfile  = logfile
        self.request  = 1
        self.lastdate = None
        self._load_last()
        self._update()

    def _load_last(self):
        if not os.path.exists(self.logfile):
            return
        with open(self.logfile, "rb") as f:
            try:
                f.seek(-4096, os.SEEK_END)
            except OSError:
                f.seek(0)
            lines = f.read().decode(errors="ignore").splitlines()
        for line in reversed(lines):
            m_req  = re.search(r"request:\s*(\d+)", line)
            m_date = re.match(r"^(\d{4}-\d{2}-\d{2})", line)
            if m_req and m_date:
                self.request  = int(m_req.group(1))
                self.lastdate = m_date.group(1)
                break

    def _update(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.lastdate == today:
            self.request += 1
        else:
            self.request  = 1
            self.lastdate = today
