"""Per-session JSONL logger."""
import json
from datetime import datetime
from pathlib import Path


class Logger:
    """Writes one JSONL file per session to log_dir/YYYYMMDD_HHMMSS.jsonl."""

    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._logfile = log_dir / f"{self.session_id}.jsonl"

    def log_user(self, content: str) -> None:
        """Append user message to session log."""
        self._write({"role": "user", "content": content, "ts": self._ts()})

    def log_tool(self, content: str) -> None:
        """Append agent tool-call result to session log."""
        self._write({"role": "user", "tool": True, "content": content, "ts": self._ts()})

    def log_assistant(
        self,
        content:    str,
        model:      str,
        tokens_in:  int | None,
        tokens_out: int | None,
        elapsed:    float,
    ) -> None:
        """Append assistant response with model and token metadata."""
        self._write({
            "role":       "assistant",
            "content":    content,
            "ts":         self._ts(),
            "model":      model,
            "tokens_in":  tokens_in,
            "tokens_out": tokens_out,
            "elapsed":    elapsed,
        })

    def _write(self, record: dict) -> None:
        with self._logfile.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _ts() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
