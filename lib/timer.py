from machine import Timer


class TimerController:
    def __init__(self):
        """
        Initialize the timer controller
        """
        self.__total_time = 0
        self.__current_time = 0

        self.__timer_counter = 0
        self.__timer_is_active = False

        self.__htimer = Timer(0)  # Hardware timer

    def get_current_time(self):
        return self.__current_time

    def get_timer_counter(self):
        return self.__timer_counter

    def increase_current_time(self):
        """
        Increase the current time and total time by 1m to maintain percentage consistency
        """
        self.__current_time += 60
        self.__total_time += 60

    def _tick(self, t):
        """
        Hardware timer callback — decreases current time by 1s
        """
        self.__current_time -= 1
        if self.__current_time <= 0:
            self.__current_time = 0

    def decrease_current_time(self):
        """
        Manual decrease — reduces current time by 60s
        """
        self.__current_time -= 60
        if self.__current_time <= 0:
            self.__current_time = 0

    def set_timer_values(self, time: int):
        """
        Set the timer values
        """
        self.__total_time = time
        self.__current_time = time

    def start_timer(self):
        """
        Start the timer
        """
        self.__htimer.init(
            period=1000, mode=Timer.PERIODIC, callback=self._tick
        )
        self.__timer_is_active = True
        self.__timer_counter += 1

    def stop_timer(self):
        """
        Stop the timer
        """
        self.__htimer.deinit()
        self.__timer_is_active = False
        self.reset_timer()

    def get_json(self):
        """
        Get time values in json format
        """
        return {
            "total_time": self.__total_time,
            "current_time": self.__current_time,
        }

    def get_timer_status(self):
        """
        Get timer status
        """
        return self.__timer_is_active

    def reset_timer(self):
        """
        Reset time values
        """
        self.__total_time = 0
        self.__current_time = 0
