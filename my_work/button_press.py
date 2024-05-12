#!/usr/bin/env python3

import zmq
from halucinator.external_devices.ioserver import IOServer
from time import sleep


def main():
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-r', '--rx_port', default=5556,
                   help='Port number to receive zmq messages for IO on')
    p.add_argument('-t', '--tx_port', default=5555,
                   help='Port number to send IO messages via zmq')
    args = p.parse_args()

    io_server = IOServer(args.rx_port, args.tx_port)
    io_server.start()

    try:
        while True:
            inp = input('Press? ')
            io_server.send_msg('Peripheral.GPIO.ext_pin_change', {'id': '0x48000800_8192', 'value': 1})
            print('sent press message...')
            sleep(5)
            io_server.send_msg('Peripheral.GPIO.ext_pin_change', {'id': '0x48000800_8192', 'value': 0})
            print('sent release message')
            sleep(1)
    except KeyboardInterrupt:
        pass

    io_server.shutdown()


if __name__ == '__main__':
    main()

