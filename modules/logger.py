# File logger for requests
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    def __init__(self, log_dir: Path):
        log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.logfile = log_dir / f"{today}.log"

    def log_request(
        self,
        model:     str,
        request:   int,
        elapsed:   float,
        token_in:  Optional[int],
        token_out: Optional[int],
        prompt:    str,
        answer:    str,
    ):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"{ts} {model}: request: {request} time: {elapsed:.1f} "
            f"tokens in: {token_in} out: {token_out}\n"
            f"\t prompt: {prompt}\n"
            f"\t answer: {answer}\n"
        )
        with self.logfile.open("a", encoding="utf-8") as f:
            f.write(entry)
