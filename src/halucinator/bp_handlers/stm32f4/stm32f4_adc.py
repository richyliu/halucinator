# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.


from ...peripheral_models.adc import ADC
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
from collections import defaultdict, deque
import struct
import binascii
import os


class STM32F4ADC(BPHandler):

    def __init__(self, model=ADC):
        self.model = ADC

    @bp_handler(['HAL_ADC_WriteAdc'])
    def write_adc(self, qemu, bp_addr):
        raise NotImplementedError


    @bp_handler(['HAL_ADC_GetValue'])
    def read_adc(self, qemu, bp_addr):
        # TODO: implement multiple ADC pins
        adc_id = '0'
        ret_val = self.model.read_adc(adc_id)
        return True, ret_val
