from timer_controller import TimerController
from motor_controller import MotorController
from sensor_controller import SensorController


class Controller:
    def __init__(
        self, sensor: SensorController, timer: TimerController, motor: MotorController
    ):
        self._sensor = sensor
        self._timer = timer
        self._motor = motor

        self.mode = None
        self.starting_temperature = 200
        self.time = 60
        self.is_active = False

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

    def run(self):
        if not self.is_active:
            return

        if not self._timer.timer_is_active:
            if self._sensor.get_temperature() >= self.starting_temperature:
                self._motor.start_motor_a()
                self._timer.set_timer_values(self.time)
                self._timer.start_timer()

        if self._timer.current_time <= 0:
            self._timer.stop_timer()
            self._motor.start_motor_b()
            self._motor.start_motor_c()
            self.deactivate()

    def stop(self):
        self._timer.stop_timer()
        self._motor.stop_motor_a()
        self._motor.stop_motor_b()
        self._motor.stop_motor_c()
        self.deactivate()

    def get_config(self):
        return {
            "mode": self.mode,
            "starting_temperature": self.starting_temperature,
            "time": self.time,
        }

    def set_config(self, mode, starting_temperature, time):
        self.mode = mode if mode is not None else self.mode
        self.starting_temperature = (
            starting_temperature
            if starting_temperature is not None
            else self.starting_temperature
        )
        self.time = time if time is not None else self.time
        return self.get_config()
