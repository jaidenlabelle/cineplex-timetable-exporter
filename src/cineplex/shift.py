from datetime import datetime

class Shift:
    """A class that represents a shift at work"""
    def __init__(self, start: datetime, end: datetime) -> None:
        self.start = start
        self.end = end