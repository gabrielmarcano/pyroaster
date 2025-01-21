from machine import Timer


class TimerController:
    def __init__(self, time_a, time_b, time_c):
        """
        Initialize the timer with no time values
        """
        self._time_a = time_a
        self._time_b = time_b
        self._time_c = time_c

        self.mani_time = 20 * 60 * 1000
        self.cacao_time = 33 * 60 * 1000
        self.cafe_time = 12 * 60 * 1000

        self._total_time = 0
        self._current_time = 0

        self.timer = Timer(0)

    def decrease_current_time(self, t):
        """
        Decrease the current time by 1000ms
        """
        self._current_time = self._current_time - 1000

    def read_time_values(self):
        """
        Get time selection from switch and calculate total and current time
        """
        if self._time_a == 0 and self._time_b == 0 and self._time_c == 0:
            self._total_time = 0
            self._current_time = 0
            return  # no time selected

        if self._time_a == 1 and self._total_time is not self.mani_time:
            self._total_time = self.mani_time
            self._current_time = self.mani_time

        if self._time_b == 1 and self._total_time is not self.cacao_time:
            self._total_time = self.cacao_time
            self._current_time = self.cacao_time

        if self._time_c == 1 and self._total_time is not self.cafe_time:
            self._total_time = self.cafe_time
            self._current_time = self.cafe_time

        if self._current_time == self._total_time:
            response = {
                "total": self._total_time,
                "current": self._current_time,
            }  # only the first time
            self.timer.init(
                period=1000, mode=Timer.PERIODIC, callback=self.decrease_current_time
            )
            return response

        response = {"total": self._total_time, "current": self._current_time}

        if self._current_time == 0:
            self.timer.deinit()
            self._total_time = 0

        return response
