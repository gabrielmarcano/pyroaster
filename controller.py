from lib.timer import TimerController
from lib.motors import MotorController
from lib.sensors import SensorController


class Controller:
    def __init__(
        self, sensor: SensorController, timer: TimerController, motor: MotorController
    ):
        self.__sensor = sensor
        self.__timer = timer
        self.__motor = motor

        self.__starting_temperature = 0
        self.__time = 0
        self.__is_active = False

    def activate(self):
        """
        Activate the controller
        """
        self.__is_active = True

    def deactivate(self):
        """
        Deactivate the controller
        """
        self.__is_active = False

    def run(self):
        """
        Run the controller logic.

        This function is starts the timer and starts the motor "A" when the temperature reaches the starting temperature.

        When the timer finishes, it starts the motor "B" and "C".
        """
        if not self.__is_active:
            return

        if not self.__timer.get_timer_status():
            if not self.__sensor.has_error() and self.__sensor.get_temperature() >= self.__starting_temperature:
                self.__motor.start_motor_a()
                self.__timer.set_timer_values(self.__time)
                self.__timer.start_timer()
        elif self.__timer.get_timer_counter() > 0 and self.__timer.get_current_time() <= 0:
            self.__timer.stop_timer()
            self.__motor.start_motor_b()
            self.__motor.start_motor_c()
            self.deactivate()

    def stop(self):
        """
        Emergency stop the controller. Also stops all motors and the timer
        """
        self.__timer.stop_timer()
        self.__motor.stop_motor_a()
        self.__motor.stop_motor_b()
        self.__motor.stop_motor_c()
        self.deactivate()

    def get_config(self):
        """
        Get the configuration of the controller in json format
        """
        return {
            "starting_temperature": self.__starting_temperature,
            "time": self.__time,
            "status": "on" if self.__is_active else "off",
        }

    def set_config(self, starting_temperature, time):
        """
        Set the configuration of the controller and return current config
        """
        if starting_temperature is not None:
            self.__starting_temperature = starting_temperature
        if time is not None:
            self.__time = time
        return self.get_config()
