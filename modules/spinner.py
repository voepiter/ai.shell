"""Animated status spinner shown while waiting for LLM response."""
import time
import threading
from . import text as ct
from . import colors as _col
from . import symbols as sym


# Displays a spinning animation in-place while the LLM request is in flight
class Spinner:
    # Initialize with request metadata shown in the spinner label
    def __init__(self, provider: str, model: str, request: int):
        self.provider    = provider
        self.model       = model
        self.request     = request
        self.start_time  = None
        self.done        = False
        self.thread      = None

    # Start the background animation thread
    def start(self):
        self.start_time = time.perf_counter()
        self.done       = False
        self.thread     = threading.Thread(target=self._run)
        self.thread.start()

    # Stop animation and clear the spinner line
    def stop(self):
        if self.done:
            return
        self.done = True
        if self.thread:
            self.thread.join()
        print("\r" + " " * 80 + "\r", end="", flush=True)

    # Animation loop — runs in a background thread until done is set
    def _run(self):
        frames = sym.spinner_frames
        frame  = 0
        while not self.done:
            elapsed = time.perf_counter() - self.start_time
            spin    = frames[frame % len(frames)]
            print(
                f"\r{_col.marker}{spin}{ct.resetcolor} "
                f"{_col.provider}{self.provider}{ct.resetcolor}"
                f"/{self.model}"
                f"  {_col.model}{elapsed:.1f}{ct.resetcolor}s ",
                end="", flush=True,
            )
            frame += 1
            time.sleep(0.1)

    # Return elapsed seconds since start; 0.0 if not started
    @property
    def elapsed(self) -> float:
        return 0.0 if self.start_time is None else time.perf_counter() - self.start_time
