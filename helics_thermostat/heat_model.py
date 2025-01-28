#!/usr/bin/env -S python3 -u

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import os
import random


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


# units are in Fahrenheit
class HeaterModel:
    def __init__(self):
        # how quickly heat is lost to the ambient environment
        self.heat_loss_rate = 0.015
        # how quickly heat is gained with the heater
        # this ratio is desired for similar behavior as the physical model
        self.heat_gain_rate = self.heat_loss_rate * 100

        self.ambient = 70
        self.temp = 90

    def update(self, dt, heater_output):
        """
        Update the internal heat model assuming some time has elapsed (dt
        in seconds) and some amount of heat (between 0 and 1 (100%)).
        """
        assert dt > 0.0
        assert 0 <= heater_output and heater_output <= 1.0

        new_temp = self.temp
        new_temp += heater_output*dt * self.heat_gain_rate
        new_temp += (self.ambient - self.temp)*dt * self.heat_loss_rate
        self.temp = new_temp

        perturbed_temp = new_temp
        # random perturbations to simulate noise
        perturbed_temp += (1 - 2*random.random()) * 0.1

        return perturbed_temp


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


def main():
    np.random.seed(628)

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateValueFederateFromConfig("helics_heat_model.json")
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

    # Physical model state
    model = HeaterModel()

    grantedtime = 0

    # Publish initial temperature to avoid undefined initial data
    new_temp = model.temp
    temp_key = "HeatModel/temperature"
    h.helicsPublicationPublishDouble(h.helicsFederateGetPublication(fed, temp_key), new_temp)
    logger.debug(f"\tPublished temperature with value " f"{new_temp:.2f}")

    # The heat model will keep simulating until finished
    while grantedtime < h.HELICS_TIME_MAXTIME:

        # Since this is the physical model, it can finish whenever
        requested_time = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
        logger.debug(f"Requesting time {requested_time}")
        nexttime = h.helicsFederateRequestTime(fed, requested_time)
        dt = nexttime - grantedtime # units: seconds
        grantedtime = nexttime
        logger.debug(f"Granted time {grantedtime}")

        if grantedtime == h.HELICS_TIME_MAXTIME:
            break

        # Update physics model
        heat_output_key = "Thermostat/heater_output"
        heat_output = h.helicsInputGetDouble(h.helicsFederateGetInputByTarget(fed, heat_output_key))
        logger.debug(f"\tReceived heat output {heat_output:.2f}")

        new_temp = model.update(dt, heat_output)

        # Publish out temperature reading
        temp_key = "HeatModel/temperature"
        h.helicsPublicationPublishDouble(h.helicsFederateGetPublication(fed, temp_key), new_temp)
        logger.debug(f"\tPublished temperature with value " f"{new_temp:.2f}")

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)


if __name__ == "__main__":
    main()

