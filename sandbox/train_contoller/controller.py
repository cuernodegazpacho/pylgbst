import time
import logging
from threading import Timer
from time import sleep
from pynput import keyboard

from pylgbst.hub import SmartHub, RemoteHandset
from pylgbst.peripherals import Voltage, Current, LEDLight, RemoteButton

MINIMUM_POWER = 0.2


# logging.basicConfig(level=logging.DEBUG)

class SimpleTrain:
    '''
    Encapsulates details of a Train. A simple train is a train *not* equipped
    with a sensor. It may or may not have a headlight. If it does, the headlight
    brightness is controlled by the motor power setting.

    For now, an instance of this class keeps tabs on the motor power
    setting, as well as battery and headlights status (if so equipped).

    This class also reports voltage and current at stdout.

    :param name: train name, used in the report
    :param report: if True, report voltage and current
    :param address: UUID of the train's internal hub

    :ivar hub: the train's internal hub
    :ivar motor: references the train's motor
    :ivar power: motor power level
    :ivar voltage: populated only when report=True
    :ivar current: populated only when report=True
    '''
    def __init__(self, name, report=False, address='86996732-BF5A-433D-AACE-5611D4C6271D'): # test hub

        self.hub = SmartHub(address=address)

        self.name = name
        self.power = 0.0
        self.voltage = 0.
        self.current = 0.
        self.motor = self.hub.port_A
        self.headlight = None

        if isinstance(self.hub.port_B, LEDLight):
            self.headlight = self.hub.port_B
            self.headlight_brightness = self.headlight.brightness

        if report:
            self._start_report()

    def _start_report(self):
        def _print_values():
            print("%s  voltage %5.2f  current %6.3f" % (self.name, self.voltage, self.current))

        def _report_voltage(value):
            self.voltage = value
            _print_values()

        def _report_current(value):
            self.current = value
            _print_values()

        self.hub.voltage.subscribe(_report_voltage, mode=Voltage.VOLTAGE_L, granularity=6)
        self.hub.current.subscribe(_report_current, mode=Current.CURRENT_L, granularity=15)

    def up_speed(self):
        self.power = min(self.power + 0.1, 1.0)
        self._set_motor_power()
        self._set_headlight_brightness()

    def down_speed(self):
        self.power = max(self.power - 0.1, -1.0)
        self._set_motor_power()
        self._set_headlight_brightness()

    def stop(self):
        self.power = 0.0
        self._set_motor_power()
        self._set_headlight_brightness()

    def _set_motor_power(self):
        self.motor.power(param=self.power)

    def _set_headlight_brightness(self, ):
        if self.headlight is not None:
            brightness = 0
            if self.power != 0.0:
                brightness = 100
            self.headlight.set_brightness(brightness)


train = SimpleTrain("Train 2", report=True) # default address references the test hub
# train hub allows handling the LED headlight.
# train = SimpleTrain("Train 1", report=True, address='F88800F6-F39B-4FD2-AFAA-DD93DA2945A6')

# Correct startup sequence requires that the train hub be connected first.
# Wait a few seconds until the train hub connects. As soon as it connects, press
# the green button on the remote handset. As soon as it connects, the control
# loop starts running. Notice that the LEDs on both train and handset will go
# solid white, and won't change color (channel) by pressing the green button.
sleep(5)
handset = RemoteHandset(address='5D319849-7D59-4EBB-A561-0C37C5EF8DCD')  # train handset

# actions associated with each handset button
speed_actions = {
    RemoteButton.PLUS: train.up_speed,
    RemoteButton.RED: train.stop,
    RemoteButton.MINUS: train.down_speed
}

# handset callback handles most of the interactive logic associated with the buttons
def handset_callback(button, set):

    # for now, ignore the right side buttons, and all button release actions.
    # This will change when we implement support for a second train.
    if set == RemoteButton.RIGHT or button == RemoteButton.RELEASE:
        return

    # select action on train speed based on which button was pressed
    speed_actions[button]()


# we can either have one single callback and handle the button set choice in the
# callback, or have two separate callbacks, one associated with each button set
# from the start. Since we are handling two trains identically, each one on one
# side of the handset, the one-callback approach prevents code duplication.
handset.port_A.subscribe(handset_callback)
handset.port_B.subscribe(handset_callback)

# Dummy main execution thread. All actions take place in the event thread.
while True:
    pass

# since this is an infinite loop, we don't care about unsubscribing from anything

