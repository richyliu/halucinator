# Timer controlled by external sources

from .peripheral import requires_tx_map, requires_rx_map, requires_interrupt_map
from . import peripheral_server
from .interrupts import Interrupts

import logging
log = logging.getLogger(__name__)
import time

# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class ExternalTimer(object):

    current_time = 0
    irq_num = 21 + 16 # TIM16 + 16 for NVIC internal

    @classmethod
    @peripheral_server.tx_msg
    def delay(cls, value):
        '''
            Device requests a delay of a certain time
        '''
        msg = {'value': value}
        cls.current_time += value
        time.sleep(0.01)
        return msg

    @classmethod
    @peripheral_server.tx_msg
    def start_timer(cls):
        msg = {'enable': True}
        Interrupts.enable_qmp(cls.irq_num)
        return msg

    @classmethod
    @peripheral_server.tx_msg
    def stop_timer(cls, value):
        msg = {'enable': True}
        return msg

    @classmethod
    @peripheral_server.reg_rx_handler
    def update_time(cls, msg):
        '''
            Update internal timer to new time received
        '''
        cls.current_time = msg['value']

    @classmethod
    @peripheral_server.reg_rx_handler
    def tick_interrupt(cls, msg):
        cls.current_time = msg['value']
        Interrupts.set_active_qmp(cls.irq_num)

    @classmethod
    def read_time(cls):
        return cls.current_time
