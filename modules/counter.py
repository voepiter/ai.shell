# Request counter — per-session sequence, starts at 1
class RequestCounter:
    def __init__(self):
        self.request = 1
