# File logger for requests
import logging
from pathlib import Path
from typing import Optional


class Logger:
    def __init__(self, logfile: Path):
        self.logfile = logfile
        self._logger = self._setup()

    def _setup(self) -> logging.Logger:
        logger = logging.getLogger("ai")
        if not logger.handlers:
            handler = logging.FileHandler(str(self.logfile), encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        return logger

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
        self._logger.info(
            f"{model}: request: {request} time: {elapsed:.1f} "
            f"tokens in: {token_in} out: {token_out} \n"
            f"\t prompt: {prompt} \n"
            f"\t answer: {answer}"
        )
