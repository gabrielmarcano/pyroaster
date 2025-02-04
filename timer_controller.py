from machine import Timer


class TimerController:
    def __init__(self):
        """
        Initialize the timer controller
        """
        self.total_time = 0
        self.current_time = 0

        self.timer_is_active = False

        self.htimer = Timer(0)  # Hardware timer

    def decrease_current_time(self, t):
        """
        Decrease the current time by 1s
        """
        self.current_time -= 1

    def set_timer_values(self, time: int):
        """
        Set the timer values
        """
        self.total_time = time
        self.current_time = time

    def start_timer(self):
        """
        Start the timer
        """
        self.htimer.init(
            period=1000, mode=Timer.PERIODIC, callback=self.decrease_current_time
        )
        self.timer_is_active = True

    def stop_timer(self):
        """
        Stop the timer
        """
        self.htimer.deinit()
        self.timer_is_active = False
        self.reset_timer()

    def get_time_values(self):
        """
        Get time values from the timer
        """
        return self.total_time, self.current_time

    def reset_timer(self):
        """
        Reset time values
        """
        self.total_time = 0
        self.current_time = 0
