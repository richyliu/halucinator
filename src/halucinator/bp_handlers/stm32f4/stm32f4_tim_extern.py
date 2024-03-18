# STM32 TIM timer, externally controlled

from ...peripheral_models.external_timer import ExternalTimer
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
import time

import logging

log = logging.getLogger(__name__)


class STM32_TIM_Extern(BPHandler):

    def __init__(self, model=ExternalTimer):
        self.model = model

    @bp_handler(['HAL_TIM_Base_Init'])
    def tim_init(self, qemu, bp_addr):
        # TODO: differentiate between different timers
        tim_obj = qemu.regs.r0
        tim_base = qemu.read_memory(tim_obj, 4, 1)

        log.info("STM32_TIM init, base: %#08x" % (tim_base))
        return False, None

    @bp_handler(['HAL_TIM_Base_Start_IT'])
    def start(self, qemu, bp_addr):
        tim_obj = qemu.regs.r0
        tim_base = qemu.read_memory(tim_obj, 4, 1)

        log.info("STM32_TIM start, base: %#08x" % tim_base)
        self.model.start_timer()
        return True, None  # Just let it run

    @bp_handler(['HAL_Delay'])
    def delay(self, qemu, bp_handler):
        amt = qemu.regs.r0
        self.model.delay(amt)
        return True, 0

    @bp_handler(['HAL_GetTick'])
    def get_tick(self, qemu, bp_addr):
        ret_val = self.model.read_time()
        return True, ret_val

