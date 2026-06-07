"""Per-session JSONL logger."""
import json
from datetime import datetime
from pathlib import Path


# Writes one JSONL file per session to log_dir/YYYYMMDD_HHMMSS.jsonl
class Logger:
    # Create log directory and open a new session file named by current timestamp
    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._logfile   = log_dir / f"{self.session_id}.jsonl"
        self._file      = self._logfile.open("a", encoding="utf-8")

    def __del__(self):
        try:
            self._file.close()
        except Exception:
            pass

    # Append user message to session log
    def log_user(self, content: str) -> None:
        self._write({"role": "user", "content": content, "ts": self._ts()})

    # Append agent tool-call result to session log
    def log_tool(self, content: str) -> None:
        self._write({"role": "tool", "content": content, "ts": self._ts()})

    # Append assistant response with model and token metadata
    def log_assistant(
        self,
        content:    str,
        model:      str,
        tokens_in:  int | None,
        tokens_out: int | None,
        elapsed:    float,
    ) -> None:
        self._write({
            "role":       "assistant",
            "content":    content,
            "ts":         self._ts(),
            "model":      model,
            "tokens_in":  tokens_in,
            "tokens_out": tokens_out,
            "elapsed":    elapsed,
        })

    # Append one record as a JSON line and flush immediately
    def _write(self, record: dict) -> None:
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._file.flush()

    # Return current time as a human-readable timestamp string
    @staticmethod
    def _ts() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
