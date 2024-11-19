#!/usr/bin/env python3

# testing for openplc device

import zmq
from halucinator.external_devices.ioserver import IOServer
from time import sleep
import random

class LocalServer(object):
    def __init__(self, ioserver):
        self.ioserver = ioserver
        ioserver.register_topic('Peripheral.GPIO.write_pin', self.write_handler)
        ioserver.register_topic('Peripheral.GPIO.toggle_pin', self.write_handler)
        ioserver.register_topic('Peripheral.ExternalTimer.delay', self.delay)
        ioserver.register_topic('Peripheral.ZmqPeripheral.hw_io', self.hw_io_handler)
        self.current_time = 0
        self.tick_delay = 1000

    def write_handler(self, ioserver, msg):
        print('got msg', msg)

    def delay(self, ioserver, msg):
        print('guest requested delay', msg)
        delay = msg['value']
        self.current_time += delay
        # update time
        d = {'value': self.current_time}
        self.ioserver.send_msg('Peripheral.ExternalTimer.update_time', d)

    def hw_io_handler(self, ioserver, msg):
        print('got hw io msg', msg)
        pass

    def tick(self):
        self.current_time += self.tick_delay
        print('updating tick to', self.current_time)
        # update time
        d = {'value': self.current_time}
        self.ioserver.send_msg('Peripheral.ExternalTimer.update_time', d)

def main():
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-r', '--rx_port', default=5556,
                   help='Port number to receive zmq messages for IO on')
    p.add_argument('-t', '--tx_port', default=5555,
                   help='Port number to send IO messages via zmq')
    args = p.parse_args()

    io_server = IOServer(args.rx_port, args.tx_port)
    server = LocalServer(io_server)

    io_server.start()

    try:
        while True:
            server.tick()
            sleep(server.tick_delay)
    except KeyboardInterrupt:
        pass
    io_server.shutdown()


if __name__ == '__main__':
    main()

