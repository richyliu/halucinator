# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from ...peripheral_models.external_timer import ExternalTimer
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
import time

import logging

log = logging.getLogger(__name__)


class STM32_Timer(BPHandler):

    def __init__(self, model=ExternalTimer):
        self.model = model

    @bp_handler(['HAL_Delay'])
    def delay(self, qemu, bp_handler):
        amt = qemu.regs.r0
        self.model.delay(amt)
        return True, 0

    @bp_handler(['HAL_GetTick'])
    def get_tick(self, qemu, bp_addr):
        ret_val = self.model.read_time()
        return True, ret_val

