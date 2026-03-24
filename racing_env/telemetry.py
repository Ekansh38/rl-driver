class LapTelemetry:
    def __init__(self):
        self.laps = []
        self._current = []

    def record(self, speed, accel, brake):
        self._current.append((speed, bool(accel), bool(brake)))

    def finish_lap(self):
        if self._current:
            self.laps.append(list(self._current))
        self._current = []
