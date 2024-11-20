# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.


from ...peripheral_models.gpio import GPIO
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
from collections import defaultdict, deque
import struct
import binascii
import os


class ArduinoGPIO(BPHandler):

    def __init__(self, model=GPIO):
        self.model = GPIO

    @bp_handler(['pinMode'])
    def set_pinmode(self, qemu, bp_addr):
        return True, 0

    @bp_handler(['digitalWrite'])
    def write_pin(self, qemu, bp_addr):
        pin = qemu.regs.r0
        value = qemu.regs.r1
        self.model.write_pin(pin, value)
        intercept = True  # Don't execute real function
        ret_val = None  # Return void
        return intercept, ret_val

    @bp_handler(['digitalRead'])
    def read_pin(self, qemu, bp_addr):
        pin = qemu.regs.r0
        intercept = True  # Don't execute real function
        ret_val = self.model.read_pin(pin)
        return intercept, ret_val
