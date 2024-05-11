#!/usr/bin/env python3

# physics environment simulation for thermostat

import zmq
from halucinator.external_devices.ioserver import IOServer
from time import sleep

def uart_write_handler(ioserver, msg):
    txt = msg['chars'].decode('latin-1')
    # print(f'UART output: "{txt.strip()}"')
    print(txt, end='', flush=True)

HEATER_GPIO = '0x48000000_256'

# units are in Fahrenheit
class HeaterModel():
    def __init__(self):
        # how quickly heat is gained with the heater
        self.heat_gain_rate = 1.0
        # how quickly heat is lost to the ambient environment
        self.heat_loss_rate = 0.01

        self.ambient = 70
        self.temp = 96

    def update(self, dt, heater_output):
        assert dt > 0.0
        assert 0 <= heater_output and heater_output <= 1.0

        new_temp = self.temp
        new_temp += heater_output*dt * self.heat_gain_rate
        new_temp += (self.ambient - self.temp)*dt * self.heat_loss_rate
        self.temp = new_temp

        return self.temp

    def to_raw(self, temp):
        return 5*temp + 192.5

    def update_to_raw(self, dt, heater_output):
        v = self.update(dt, heater_output)
        return self.to_raw(v)

class LocalServer(object):
    def __init__(self, ioserver):
        self.ioserver = ioserver
        ioserver.register_topic('Peripheral.GPIO.write_pin', self.write_handler)
        ioserver.register_topic('Peripheral.GPIO.toggle_pin', self.write_handler)
        ioserver.register_topic('Peripheral.ExternalTimer.delay', self.delay)
        ioserver.register_topic('Peripheral.ExternalTimer.start_timer', self.start_timer)
        ioserver.register_topic('Peripheral.ZmqPeripheral.hw_io', self.hw_io_handler)
        self.current_time = 0
        self.timer_active = False

        # internal model values
        self.heater_model = HeaterModel()

        # input state values (initial)
        self.heater_gpio = True

        # TODO: calculate tick times from based on guest options
        self.timer_frequency = 76.5/1000.0

    def write_handler(self, ioserver, msg):
        if msg['id'] == HEATER_GPIO:
            state = msg['value'] == 1
            self.heater_gpio = state

    def hw_io_handler(self, ioserver, msg):
        # pwm is at address 0x40012c34
        if msg['offset'] == 0x12c34:
            state = msg['value']
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

        # update model values
        heater_proportion = self.heater_gpio/65535.0
        dt = self.timer_frequency

        raw = self.heater_model.update_to_raw(dt, heater_proportion)

        # print('heat:', int(self.heater_model.temp), 'raw:', raw, 'pwm output:', int(heater_proportion * 1000)/1000.0)
        self.ioserver.send_msg('Peripheral.ADC.ext_adc_change', {'id': '0', 'value': int(raw)})

        self.current_time += self.timer_frequency * 1000

        # reset inputs before calling interrupt (which would get us the next values)
        self.heater_gpio = None

        self.ioserver.send_msg('Peripheral.ExternalTimer.tick_interrupt', {'value': int(self.current_time)})

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
            server.tick()
    except KeyboardInterrupt:
        pass
    io_server.shutdown()
    # io_server.join()


if __name__ == '__main__':
    main()
