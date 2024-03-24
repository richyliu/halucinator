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
        ioserver.register_topic('Peripheral.GPIO.report_pwm_val', self.pwm_write_handler)
        ioserver.register_topic('Peripheral.ExternalTimer.delay', self.delay)
        ioserver.register_topic('Peripheral.ExternalTimer.start_timer', self.start_timer)
        self.current_time = 0
        self.timer_active = False

        # internal model values
        self.adc = 3735

        # input state values (initial)
        self.heater_gpio = True

    def write_handler(self, ioserver, msg):
        if msg['id'] == HEATER_GPIO:
            state = msg['value'] == 1
            if HEATER_ACTIVE_LOW:
                state = not state
            self.heater_gpio = state

    def pwm_write_handler(self, ioserver, msg):
        if msg['id'] == HEATER_GPIO:
            state = msg['value']
            print('pwm value:', state)
            self.heater_gpio = state

    def delay(self, ioserver, msg):
        delay = msg['value']
        self.current_time += delay
        # update time
        d = {'value': self.current_time}
        self.ioserver.send_msg('Peripheral.ExternalTimer.update_time', d)
        self.update_model()

    def tick(self):
        if not self.timer_active:
            return

        # wait until we have all inputs
        if self.heater_gpio is None:
            return

        print('tick.')

        # update model values
        if self.heater_gpio > 1:
            self.adc += self.heater_gpio/4096.0
        if self.heater_gpio:
            self.adc += 1
        else:
            self.adc -= 1
        self.ioserver.send_msg('Peripheral.ADC.ext_adc_change', {'id': '0', 'value': int(self.adc)})

        # TODO: calculate tick times from based on guest options
        self.current_time += 10

        # reset inputs before calling interrupt (which would get us the next values)
        self.heater_gpio = None

        self.ioserver.send_msg('Peripheral.ExternalTimer.tick_interrupt', {'value': self.current_time})

    def start_timer(self, ioserver, msg):
        print('starting timer')
        self.timer_active = True

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
    io_server.register_topic(
        'Peripheral.UARTPublisher.write', uart_write_handler)

    io_server.start()

    # print('TODO: just testing')
    # io_server.send_msg('Peripheral.ExternalTimer.tick_interrupt', {'value': 1234})
    # io_server.shutdown()
    # return

    try:
        while True:
            sleep(0.5)
            server.tick()
    except KeyboardInterrupt:
        pass
    io_server.shutdown()
    # io_server.join()


if __name__ == '__main__':
    main()
