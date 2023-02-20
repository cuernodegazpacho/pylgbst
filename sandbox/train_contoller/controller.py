import time
import logging
from time import sleep
from pynput import keyboard

from pylgbst.hub import SmartHub, RemoteHandset
from pylgbst.peripherals import Voltage, RemoteButton

# logging.basicConfig(level=logging.DEBUG)

class Train:
    '''
    Encapsulates details of a Train. For now, it keeps tabs on its motor power
    setting, as well as battery voltage and headlights status (if so equipped).

    This class also reports voltage and current at stdout.

    :param address: UUID of the train's internal hub

    :ivar hub: the train's internal hub
    :ivar power: the current motor power level
    '''
    def __init__(self, address='86996732-BF5A-433D-AACE-5611D4C6271D'): # test hub
        self.hub = SmartHub(address=address)

        self.power = 0.0

    def up_speed(self):
        self.power = min(self.power + 0.1, 1.0)
        self._set_motor_power()

    def down_speed(self):
        self.power = max(self.power - 0.1, -1.0)
        self._set_motor_power()

    def stop(self):
        self.power = 0.0
        self._set_motor_power()

    def _set_motor_power(self):
        self.hub.port_A.power(param=self.power)



train = Train()

# wait a few seconds until the train hub connects. As soon as it connects, press
# the green button on the remote handset. As soon as it connects, the control
# loop starts running.
sleep(5)
handset = RemoteHandset(address='5D319849-7D59-4EBB-A561-0C37C5EF8DCD')  # train handset

# actions associated to each handset button
actions = {
    RemoteButton.PLUS: train.up_speed,
    RemoteButton.MINUS: train.down_speed,
    RemoteButton.RED: train.stop,
}

# handset callback handles most of the interactive logic
def handset_callback(button, set):

    # ignore the right buttons and all button release actions.
    if set == RemoteButton.RIGHT or button == RemoteButton.RELEASE:
        return

    # action on train speed
    actions[button]()


# we can either have one single callback and handle the button set in the
# callback, or have two separate callbacks, one associated to each button
# set from the start. Since we are handling two trains, each one on one
# side of the handset, the one-callback approach prevents code duplication.
handset.port_A.subscribe(handset_callback)
handset.port_B.subscribe(handset_callback)

# Dummy main execution thread.
while True:
    print("@@@@ controller.py 53: " )
    sleep(1)

