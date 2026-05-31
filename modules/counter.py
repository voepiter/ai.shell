"""Per-session request counter, starts at 1."""


# Tracks request number displayed in stats line
class RequestCounter:
    def __init__(self):
        self._n = 1

    # Return current request number and advance the counter
    def next(self) -> int:
        n = self._n
        self._n += 1
        return n
