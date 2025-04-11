from ...peripheral_models.adc import ADC
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
from collections import defaultdict, deque
import struct
import binascii
import os


class ArduinoADC(BPHandler):

    def __init__(self, model=ADC):
        self.model = ADC

    @bp_handler(['analogWrite'])
    def write_adc(self, qemu, bp_addr):
        raise NotImplementedError


    @bp_handler(['analogRead'])
    def read_adc(self, qemu, bp_addr):
        adc_id = qemu.regs.r0
        ret_val = self.model.read_adc(adc_id)
        return True, ret_val
