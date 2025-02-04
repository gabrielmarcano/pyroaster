class MotorController:
    def __init__(self, motor_a, motor_b, motor_c):
        """
        Initialize the motor controller
        """
        self._motor_a = motor_a
        self._motor_b = motor_b
        self._motor_c = motor_c

        self.motor_a_is_active = False
        self.motor_b_is_active = False
        self.motor_c_is_active = False

    def read_motor_states(self):
        """
        Get time selection from switch and calculate total and current time
        """
        return self._motor_a.value(), self._motor_b.value(), self._motor_c.value()

    def start_motor_a(self):
        """
        Start motor A
        """
        self._motor_a.on()
        self.motor_a_is_active = True

    def stop_motor_a(self):
        """
        Stop motor A
        """
        self._motor_a.off()
        self.motor_a_is_active = False

    def start_motor_b(self):
        """
        Start motor B
        """
        self._motor_b.on()
        self.motor_b_is_active = True

    def stop_motor_b(self):
        """
        Stop motor B
        """
        self._motor_b.off()
        self.motor_b_is_active = False

    def start_motor_c(self):
        """
        Start motor C
        """
        self._motor_c.on()
        self.motor_c_is_active = True

    def stop_motor_c(self):
        """
        Stop motor C
        """
        self._motor_c.off()
        self.motor_c_is_active = False
