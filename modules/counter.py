"""Per-session request counter, starts at 1."""

# Tracks request number displayed in spinner and stats
class RequestCounter:
    def __init__(self):
        self.request = 1
