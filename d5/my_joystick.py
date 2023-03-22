
from donkeycar.parts.controller import Joystick, JoystickController


class MyJoystick(Joystick):
    #An interface to a physical joystick available at /dev/input/js0
    def __init__(self, *args, **kwargs):
        super(MyJoystick, self).__init__(*args, **kwargs)

            
        self.button_names = {
            0x130 : 'A',
            0x133 : 'X',
            0x134 : 'Y',
            0x131 : 'B',
            0x136 : 'LB',
            0x137 : 'RB',
            0x13d : 'L_dpad_down',
        }


        self.axis_names = {
            0x10 : 'left_steer',
            0x4 : 'right_acc',
            0x5 : 'RT',
            0x2 : 'LT',
        }



class MyJoystickController(JoystickController):
    #A Controller object that maps inputs to actions
    def __init__(self, *args, **kwargs):
        super(MyJoystickController, self).__init__(*args, **kwargs)


    def init_js(self):
        #attempt to init joystick
        try:
            self.js = MyJoystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            print(self.dev_fn, "not found.")
            self.js = None
        return self.js is not None


    def init_trigger_maps(self):
        #init set of mapping from buttons to function calls
            
        self.button_down_trigger_map = {
            'RB' : self.increase_max_throttle,
            'LB' : self.decrease_max_throttle,
            'B' : self.emergency_stop,
            'A' : self.erase_last_N_records,
            'X' : self.toggle_mode,
            'Y' : self.toggle_constant_throttle,
            'L_dpad_down' : self.toggle_manual_recording,
        }


        self.axis_trigger_map = {
            'left_steer' : self.set_steering,
            'RT' : self.set_throttle,
        }


