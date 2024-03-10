#!/usr/bin/env python3

# physics environment simulation for thermostat

import zmq
from halucinator.external_devices.ioserver import IOServer
from time import sleep

def uart_write_handler(ioserver, msg):
    txt = msg['chars'].decode('latin-1')
    print(f'UART output: "{txt.strip()}"')

HEATER_GPIO = '0x48000000_256'
HEATER_ACTIVE_LOW = True

class LocalServer(object):
    def __init__(self, ioserver):
        self.ioserver = ioserver
        ioserver.register_topic('Peripheral.GPIO.write_pin', self.write_handler)
        ioserver.register_topic('Peripheral.GPIO.toggle_pin', self.write_handler)
        ioserver.register_topic('Peripheral.ExternalTimer.delay', self.delay)
        self.current_time = 0

        # internal model values
        self.global_heater_on = False
        self.adc = 3735

    def write_handler(self, ioserver, msg):
        if msg['id'] == HEATER_GPIO:
            state = msg['value'] == 1
            if HEATER_ACTIVE_LOW:
                state = not state
            self.global_heater_on = state

    def delay(self, ioserver, msg):
        delay = msg['value']
        self.current_time += delay
        # update time
        d = {'value': self.current_time}
        self.ioserver.send_msg('Peripheral.ExternalTimer.update_time', d)
        self.update_model()

    def update_model(self):
        # update model values
        if self.global_heater_on:
            self.adc += 1
        else:
            self.adc -= 1
        self.ioserver.send_msg('Peripheral.ADC.ext_adc_change', {'id': '0', 'value': self.adc})

def main():
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-r', '--rx_port', default=5556,
                   help='Port number to receive zmq messages for IO on')
    p.add_argument('-t', '--tx_port', default=5555,
                   help='Port number to send IO messages via zmq')
    args = p.parse_args()

    io_server = IOServer(args.rx_port, args.tx_port)
    LocalServer(io_server)
    io_server.register_topic(
        'Peripheral.UARTPublisher.write', uart_write_handler)

    io_server.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass
    io_server.shutdown()
    # io_server.join()


if __name__ == '__main__':
    main()
