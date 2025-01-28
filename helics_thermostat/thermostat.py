#!/usr/bin/env -S python3 -u

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import os
import subprocess
import time
from halucinator.external_devices.ioserver import IOServer


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)


def destroy_federate(fed):
    """
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate. Doing so informs the rest of the
    federation that it is no longer a part of the co-simulation and they
    should proceed without it (if applicable). Generally this is done
    when the co-simulation is complete and all federates end execution
    at more or less the same wall-clock time.

    :param fed: Federate to be destroyed
    :return: (none)
    """
    
    # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info("Federate finalized")


class ThermostatManager:
    def __init__(self, hal_ports=(5556, 5555)):
        # same as the defines in Core/Src/main.c for the thermostat
        self.RAW_TO_TEMP_A = 0.175
        self.RAW_TO_TEMP_B = -22.2

        self.HEATER_GPIO = '0x48000000_256'

        self._proc = None
        self._hal_rx_port, self._hal_tx_port = hal_ports
        self._booted = False

        self.heater_output = None

    def _update_heater_output(self, value):
        if self.heater_output is not None:
            logger.warning(f"\tDiscarded unused heater output reading {self.heater_output}")
        self.heater_output = value

    def start(self):
        assert self._proc is None, "attempting to start a process that is already running"
        logger.info("Starting halucinator.")

        def gpio_write_handler(ioserver, msg):
            if msg['id'] == self.HEATER_GPIO:
                self._update_heater_output(msg['value'])

        def hw_io_handler(ioserver, msg):
            # pwm is at address 0x40012c34
            if msg['offset'] == 0x12c34:
                raw_heater_value = int(msg['value'])
                heater_proportion = raw_heater_value / 65535.0
                self._update_heater_output(heater_proportion)

        def uart_write_handler(ioserver, msg):
            txt = msg['chars'].decode('latin-1')
            if 'Boot.' in txt:
                self._booted = True
            logger.debug(f"\tGot UART message: '{txt}'")
            print(txt, end='', flush=True)

        logger.debug(f"Creating halucinator IOServer({self._hal_rx_port}, {self._hal_tx_port})")
        self.io_server = IOServer(self._hal_rx_port, self._hal_tx_port)
        self.io_server.register_topic('Peripheral.GPIO.write_pin', gpio_write_handler)
        self.io_server.register_topic('Peripheral.GPIO.toggle_pin', gpio_write_handler)
        self.io_server.register_topic('Peripheral.ZmqPeripheral.hw_io', hw_io_handler)
        self.io_server.register_topic('Peripheral.UARTPublisher.write', uart_write_handler)
        self.io_server.start()

        self._proc = subprocess.Popen(
                ['./run.sh'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
                )

        # wait for halucinated thermostat to boot
        while not self._booted:
            time.sleep(0.001)

        logger.info("Started halucinator process and IO server")

    def stop(self):
        assert self._proc, "cannot stop a process that is not running"
        self._proc.terminate()
        self.io_server.shutdown()

    def _temp_to_raw(self, temp):
        return (temp - self.RAW_TO_TEMP_B)/self.RAW_TO_TEMP_A

    def update(self, temp, cur_time):
        """
        Update the thermostat with a new temperature (unit: F) reading at the
        current time (in seconds). Return the new output control value. This
        function may block when simulating the thermostat code.
        """

        assert self._proc is not None, "cannot update when thermostat process not running"

        # reset value to wait for
        self.heater_output = None

        # send in new readings
        raw = self._temp_to_raw(temp)
        logger.debug(f"\tSending temp (raw): {raw} to halucinator")
        self.io_server.send_msg('Peripheral.ADC.ext_adc_change', {'id': '0', 'value': int(raw)})

        # trigger interrupt, telling device to process new inputs
        ticks = int(cur_time * 1000)
        self.io_server.send_msg('Peripheral.ExternalTimer.tick_interrupt', {'value': ticks})

        # wait until we have all inputs
        raw_reading = self.heater_output
        while raw_reading is None:
            raw_reading = self.heater_output
            time.sleep(0.001)

        logger.debug(f"\tGot heater output: {raw_reading}")

        return raw_reading


def main():
    np.random.seed(628)

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateValueFederateFromConfig("helics_thermostat.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    subid = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsInputGetTarget(subid[i])
        logger.debug(f"\tRegistered subscription---> {sub_name}")

    pubid = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(pubid[i])
        logger.debug(f"\tRegistered publication---> {pub_name}")

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    # Init thermostat
    thermostat = ThermostatManager()
    thermostat.start()

    update_interval = 76.5/1000.0 # must match time_delta in helics_thermostat.json
    total_interval = update_interval * 25
    grantedtime = 0

    # Data collection lists
    time_sim = []
    outputs = []
    temps = []

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")

        # Get new sensor readings
        thermometer_key = "HeatModel/temperature"
        temp = h.helicsInputGetDouble(h.helicsFederateGetInputByTarget(fed, thermometer_key))
        logger.debug(f"\tReceived temperature {temp:.2f}")

        # Update thermostat with new inputs from physics model
        output = thermostat.update(temp, grantedtime)

        # Publish out new heater output
        heat_output_key = "Thermostat/heater_output"
        h.helicsPublicationPublishDouble(h.helicsFederateGetPublication(fed, heat_output_key), output)
        logger.debug(f"\tPublished output with value " f"{output:.2f}")

        # Data collection vectors
        time_sim.append(grantedtime)
        outputs.append(output)
        temps.append(temp)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    thermostat.stop()

    # Output graph showing the heater output level and the temperature
    xaxis = np.array(time_sim)
    y_outputs = np.array(outputs)
    y_temps = np.array(temps)

    fig, axs = plt.subplots(2, sharex=True)
    fig.suptitle("Thermostat control over time")

    axs[0].plot(xaxis, y_outputs, color="tab:blue", linestyle="-")
    axs[0].set(ylabel="%")
    axs[0].grid(True)

    axs[1].plot(xaxis, y_temps, color="tab:blue", linestyle="-")
    axs[1].set(ylabel="F")
    axs[1].grid(True)

    plt.xlabel("time (sec)")
    plt.savefig("thermostat_plot.png", format="png")

    plt.show()


if __name__ == "__main__":
    main()
