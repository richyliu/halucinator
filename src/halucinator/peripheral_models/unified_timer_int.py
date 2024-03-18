"""
A unified timer interrupt based system.

This is designed to support emulating firmware that uses timer interrupt-driven
code. Each interrupt is triggered by an external source, supplying new values (inputs)
for any I/O or function reads. Function writes (outputs) are sent as they
become available.
"""

from .peripheral import requires_tx_map, requires_rx_map, requires_interrupt_map
from . import peripheral_server
from collections import defaultdict

import logging
log = logging.getLogger(__name__)
# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class GPIO(object):

    DEFAULT = 0
    gpio_state = defaultdict(int)

    @classmethod
    @peripheral_server.tx_msg
    def write_pin(cls, gpio_id, value):
        '''
            Creates the message that peripheral_server.tx_msg will send on this 
            event
        '''
        GPIO.gpio_state[gpio_id] = value
        msg = {'id': gpio_id, 'value': value}
        log.debug("GPIO.write_pin " + repr(msg))
        return msg

    @classmethod
    @peripheral_server.tx_msg
    def toggle_pin(cls, gpio_id):
        '''
            Creates the message that Peripheral.tx_msga will send on this 
            event
        '''
        if gpio_id not in GPIO.gpio_state:
            GPIO.gpio_state[gpio_id] = 0
        else:
            GPIO.gpio_state[gpio_id] = GPIO.gpio_state[gpio_id] ^ 1

        msg = {'id': gpio_id, 'value': GPIO.gpio_state[gpio_id]}
        log.debug("GPIO.toggle_pin " + repr(msg))
        return msg

    @classmethod
    @peripheral_server.reg_rx_handler
    def ext_pin_change(cls, msg):
        '''
            Processes reception of messages from external 0mq server
            type is GPIO.zmq_set_gpio
        '''
        print("GPIO.ext_pin_change", msg)
        gpio_id = msg['id']
        value = msg['value']
        GPIO.gpio_state[gpio_id] = value

    @classmethod
    def read_pin(cls, pin_id):
        return GPIO.gpio_state[pin_id]

