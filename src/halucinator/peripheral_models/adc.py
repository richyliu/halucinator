# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from .peripheral import requires_tx_map, requires_rx_map, requires_interrupt_map
from . import peripheral_server
from collections import defaultdict

import logging
log = logging.getLogger(__name__)
# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class ADC(object):

    DEFAULT = 0
    adc_state = defaultdict(int)

    @classmethod
    @peripheral_server.tx_msg
    def write_value(cls, adc_id, value):
        raise NotImplementedError

    @classmethod
    @peripheral_server.reg_rx_handler
    def ext_adc_change(cls, msg):
        '''
            Processes reception of messages from external 0mq server
        '''
        print("ADC.ext_adc_change", msg)
        adc_id = msg['id']
        value = msg['value']
        ADC.adc_state[adc_id] = value

    @classmethod
    def read_adc(cls, adc_id):
        return ADC.adc_state[adc_id]
