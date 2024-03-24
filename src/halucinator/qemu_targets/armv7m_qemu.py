# Copyright 2021 National Technology & Engineering Solutions of Sandia, LLC 
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, 
# the U.S. Government retains certain rights in this software.

from .arm_qemu import ARMQemuTarget

import struct

class ARMv7mQemuTarget(ARMQemuTarget):

    def trigger_interrupt(self, interrupt_number, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-inject-irq',
            {'num_irq': interrupt_number, 'num_cpu': cpu_number})

    def set_vector_table_base(self, base, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-set-vector-table-base',
            {'base': base, 'num_cpu': cpu_number})

    def enable_interrupt(self, interrupt_number, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-enable-irq',
            {'num_irq': interrupt_number, 'num_cpu': cpu_number})

    def write_branch(self, addr, branch_target, options=None):
        '''
            Places an absolute branch at address addr to
            branch_target

            :param addr(int): Address to write the branch code to
            :param branch_target: Address to branch too
        '''
        instrs = []
        instrs.append(self.assemble("ldr r4, [pc, #0]"))  # PC is 2 instructions ahead
        instrs.append(self.assemble("bx r4"))
        instrs.append(struct.pack("<I", branch_target))  # Address of callee
        instructions = b"".join(instrs)

        # Write to 2-byte aligned address in case LSB is set to indicate thumb
        # mode. We do this because addr may have LSB set in the symbol table,
        # but we want to clear it to write the "actual" address.
        addr &= ~0x1

        self.write_memory(addr, 1, instructions, len(instructions), raw=True)
