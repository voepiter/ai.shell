"""Per-session request counter, starts at 1."""
class RequestCounter:
    def __init__(self):
        self.request = 1
