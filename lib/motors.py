class MotorController:
    def __init__(self, motor_a, motor_b, motor_c):
        """
        Initialize the motor controller
        """
        self.__motor_a = motor_a
        self.__motor_b = motor_b
        self.__motor_c = motor_c

        self.__motor_a_is_active = False
        self.__motor_b_is_active = False
        self.__motor_c_is_active = False

    def read_motor_states(self):
        """
        Read the state of the motors
        """
        return self.__motor_a.value(), self.__motor_b.value(), self.__motor_c.value()

    def get_json(self):
        """
        Get the state of the motors in json format
        """
        # TODO: change read_motor_states to return boolean values
        return {
            "motor_a": self.__motor_a.value(),
            "motor_b": self.__motor_b.value(),
            "motor_c": self.__motor_c.value(),
        }

    def start_motor_a(self):
        """
        Start motor A
        """
        self.__motor_a.on()
        self.__motor_a_is_active = True

    def stop_motor_a(self):
        """
        Stop motor A
        """
        self.__motor_a.off()
        self.__motor_a_is_active = False

    def start_motor_b(self):
        """
        Start motor B
        """
        self.__motor_b.on()
        self.__motor_b_is_active = True

    def stop_motor_b(self):
        """
        Stop motor B
        """
        self.__motor_b.off()
        self.__motor_b_is_active = False

    def start_motor_c(self):
        """
        Start motor C
        """
        self.__motor_c.on()
        self.__motor_c_is_active = True

    def stop_motor_c(self):
        """
        Stop motor C
        """
        self.__motor_c.off()
        self.__motor_c_is_active = False
