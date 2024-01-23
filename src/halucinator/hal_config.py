# Copyright 2021 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS,
# the U.S. Government retains certain rights in this software.

"""
Primary parser and validator of halucinator config file
"""
import csv
import importlib
import inspect
import logging
import os
import sys
from struct import unpack
import yaml

from halucinator import hal_log as hal_log_conf
from halucinator.config.target_archs import HALUCINATOR_TARGETS
from halucinator.config.elf_program import ELFProgram
from halucinator.config.memory_config import HalMemConfig
from halucinator.config.symbols_config import HalSymbolConfig

log = logging.getLogger(__name__)
hal_log = hal_log_conf.getHalLogger()


class HalInterceptConfig:
    """
    Intercepts entries in config file are mapped to
    this class
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        config_file,
        cls,
        function,
        addr=None,
        symbol=None,
        class_args=None,
        registration_args=None,
        run_once=False,
        watchpoint=False,
    ):  # pylint: disable=too-many-instance-attributes,too-many-arguments
        self.config_file = config_file
        self.symbol = symbol

        self.bp_addr = addr

        self.cls = cls
        self.function = function
        self.class_args = class_args if class_args is not None else {}
        if "self" in self.class_args:
            del self.class_args["self"]
        self.registration_args = (
            registration_args if registration_args is not None else {}
        )
        if "self" in self.registration_args:
            del self.registration_args["self"]
        self.run_once = run_once
        self.watchpoint = watchpoint  # Valid 'r', 'w' ,'rw'

    def _check_handler_is_valid(self):
        """
        Checks if the handler specified in the config
        is valid
        """
        valid = True
        split_str = self.cls.split(".")
        module_str = ".".join(split_str[:-1])
        class_str = split_str[-1]
        try:
            module = importlib.import_module(module_str)
        except ImportError:
            hal_log.error("No module %s on Intercept %s", module_str, self)
            return False

        cls_obj = getattr(module, class_str, None)
        if cls_obj is None:
            hal_log.error("Intercept No Class for %s", self)
            return False

        # See if could init class
        argspec = inspect.signature(cls_obj.__init__)
        if not set(self.class_args).issubset(set(argspec.parameters)):
            hal_log.error("class_arg are invalid for %s", self)
            hal_log.error("    Valid options %s", argspec.parameters)
            hal_log.error("    Input options %s", self.class_args)
            valid = False

        argspec = inspect.signature(cls_obj.register_handler)
        if not set(self.registration_args).issubset(set(argspec.parameters)):
            hal_log.error("class_arg are invalid for %s", self)
            hal_log.error("    Valid options %s", argspec.parameters)
            hal_log.error("    Input options %s", self.registration_args)
            valid = False
        return valid

    def is_valid(self):
        """
        Used to check if intercept is valid
        """
        valid = True

        if self.watchpoint not in (False, "r", "w", "rw", True):
            hal_log.error(
                "Intercept: Watchpoints must be false, true, r, w, or rw on: %s", self
            )
            valid = False

        valid &= self._check_handler_is_valid()

        if self.bp_addr is not None and not isinstance(self.bp_addr, int):
            hal_log.error("Intercept addr invalid\n\t%s", self)
            valid = False
        return valid

    def __repr__(self):
        if not isinstance(self.bp_addr, int):
            return (
                "({self.config_file})\\[symbol: {self.symbol}, "
                f"class: {self.cls}, function:{self.function}]"
            )
        return (
            f"({self.config_file})\\[symbol: {self.symbol}, addr: {hex(self.bp_addr)}, "
            f"class: {self.cls}, function:{self.function}]"
        )


class HALMachineConfig:
    """
    This class encapsulates the machine entry in the
    config file and provides helper methods to access
    its components and to validate the config.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        config_file=None,
        arch="cortex-m3",
        cpu_model="cortex-m3",
        entry_addr=None,
        init_sp=None,
        gdb_exe="gdb-multiarch",
        vector_base=0x08000000,
        gdb_arch=None,
        machine=None,
    ):  # pylint: disable=too-many-arguments
        self.arch = arch
        self.machine = machine
        self.cpu_model = cpu_model
        self.entry_addr = entry_addr
        self.init_sp = init_sp
        self.gdb_exe = gdb_exe
        self.gdb_arch = gdb_arch
        self.vector_base = vector_base
        self.config_file = config_file
        self.using_default_machine = config_file is None

        if self.arch not in HALUCINATOR_TARGETS:
            hal_log.critical(
                "Arch %s not supported.  Supported Archs: %s",
                self.arch,
                HALUCINATOR_TARGETS.keys,
            )

    def get_avatar_arch(self):
        """
        Returns the Avatar Architecture
        """
        return HALUCINATOR_TARGETS[self.arch]["avatar_arch"]

    def get_qemu_target(self):
        """
        Returns the QEMU Target
        """
        return HALUCINATOR_TARGETS[self.arch]["qemu_target"]

    def get_qemu_path(self):
        """
        Returns path for starting qemu
        """
        arch_info = HALUCINATOR_TARGETS[self.arch]
        if "qemu_env_var" in arch_info.keys():
            var = arch_info["qemu_env_var"]
            if os.environ.get(var) is not None:
                if not os.path.exists(os.environ.get(var)):
                    log.error("Path ENV VAR $%s is invalid", var)
                    sys.exit(1)
                return os.environ.get(var)

        if os.path.exists(arch_info["qemu_default_path"]):
            log.info("Using QEMU from default path: %s", arch_info["qemu_default_path"])
            return arch_info["qemu_default_path"]
        else:
            log.error("No qemu path: %s", arch_info["qemu_default_path"])

        log.critical("No QEMU path for %s", self.arch)
        sys.exit(1)
        return None

    def __repr__(self):
        return (
            f"({self.arch}) Machine arch:{self.arch}, cpu_type:{self.cpu_model}, "
            f"entry_addr:{hex(self.entry_addr)}, gdb_exe:{self.gdb_exe}"
        )


class HalucinatorConfig:
    # pylint: disable=too-many-instance-attributes
    """
    This class encapsulates the halucinator
    config file(s) and provides helper methods to access
    its components and to validate the config.
    """

    def __init__(self):

        self.machine = HALMachineConfig()
        self.options = {}
        self.memories = {}
        self.intercepts = []
        self.watchpoints = []
        self.symbols = []
        self.callables = []
        self.elf_program = None

    def add_yaml(self, yaml_filename):
        """
        Opens and parses a yaml file adding it contents
        to this config
        """
        with open(yaml_filename, "rb") as infile:
            part_config = yaml.load(infile, Loader=yaml.FullLoader)

            if "machine" in part_config:
                self._parse_machine(part_config["machine"], yaml_filename)
            if "memories" in part_config:
                self._parse_memory(part_config["memories"], yaml_filename)
            if "peripherals" in part_config:
                # Same as memories except requires emulate field
                self._parse_memory(part_config["peripherals"], yaml_filename, True)
            if "intercepts" in part_config:
                self._parse_intercepts(part_config["intercepts"], yaml_filename)
            if "symbols" in part_config:
                self._parse_symbols(part_config["symbols"], yaml_filename)
            if "options" in part_config:
                self.options.update(part_config["options"])
            if "elf_program" in part_config:
                self._parse_elf_program(part_config["elf_program"], yaml_filename)

    def add_csv_symbols(self, csv_file):
        """
        Reads in a file of csv with format
        symbol_name, first_addr, last_addr
        """
        with open(csv_file, "r") as infile:  # pylint: disable=unspecified-encoding
            reader = csv.reader(infile)
            for row in reader:
                addr = int(row[1].strip(), 0)
                addr2 = int(row[2].strip(), 0)
                size = addr2 - addr
                self.symbols.append(
                    HalSymbolConfig(csv_file, row[0].strip(), addr, size)
                )

    def _parse_machine(self, machine_dict, filename):
        """
        Parse the machine entry from the config file
        """
        prev_machine = self.machine
        self.machine = HALMachineConfig(filename, **machine_dict)
        if not prev_machine.using_default_machine:
            hal_log.warning(
                "Overwriting previous machine %s with %s", prev_machine, self.machine
            )

    def _parse_memory(self, mem_dict, yaml_filename, emulate_required=False):
        """
        Parsers memory config from yaml file.
        """
        if not hasattr(mem_dict, "items"):
            return

        for mem_name, mem_conf in mem_dict.items():
            new_mem = HalMemConfig(mem_name, yaml_filename, **mem_conf)
            new_mem.emulate_required = emulate_required

            for _, old_mem in self.memories.items():
                if mem_name == old_mem.name:
                    hal_log.warning(
                        "Memory Config Overwritten:\n\tOld:%s\n\tNew:%s",
                        old_mem,
                        new_mem,
                    )

            self.memories[mem_name] = new_mem

    def _parse_elf_program(self, elf_dict, yaml_file):
        """
        Parse the elf program entry from the config file
        """
        self.elf_program = ELFProgram(yaml_file, elf_dict, self)
        if self.elf_program.execute_before:
            self.elf_program.exit_to = self.machine.entry_addr
            self.machine.entry_addr = self.elf_program.get_entry_addr()

    def _parse_intercepts(self, intercept_lst, yaml_file):
        """
            Parse the intercept entries from the config file
            expect the below format.

        intercepts:
            - class: halucinator.bp_handlers.SkipFunc (must be BPHandler sub class)
              addr: (firmware function_name or address) #
              function: BSP_IO_WritePin     # Intercept function name
        """
        if intercept_lst is not None:
            for int_conf in intercept_lst:
                int_conf["cls"] = int_conf["class"]
                del int_conf["class"]
                intercept = HalInterceptConfig(yaml_file, **int_conf)
                self.intercepts.append(intercept)

    def _parse_symbols(self, sym_dict, yaml_file):
        """
        Parses the symbol entry from the config file
        """
        for addr, sym_name in sym_dict.items():
            sym = HalSymbolConfig(yaml_file, name=sym_name, addr=addr)
            self.symbols.append(sym)

    def get_addr_for_symbol(self, sym_name):
        """
        Gets that address for specified symbol

        :param sym_name:  Name of the symbol
        :ret_val None or Address:
        """
        for sym in self.symbols:
            if sym_name == sym.name:
                return sym.addr
        return None

    def resolve_intercept_bp_addrs(self):
        """
        Gets all the address of all symbols in intercepts and sets the address
        appropriately.
        """
        log.debug("Resolving Symbols")
        for inter in self.intercepts:
            if inter.bp_addr is None:
                sym_name = inter.symbol if inter.symbol is not None else inter.function
                addr = self.get_addr_for_symbol(sym_name)
                if addr is not None:
                    inter.bp_addr = addr
                    log.debug("Resolved symbol: %s, %#x", inter.symbol, addr)
                else:
                    log.warning("Unresolved symbol: %s, %s", inter.symbol, inter)

    def get_symbol_name(self, addr):
        """
        Gets symbol name that contains address
        """
        for sym in self.symbols:
            # pylint: disable=chained-comparison
            if addr >= sym.addr and addr <= (sym.addr + sym.size):
                return sym.name
        return hex(addr)

    def memory_by_name(self, name):
        """
        Finds the memory with a given name

        :param name:  Name to find memory for
        :ret (memory, or None:
        """
        for m_name, mem in self.memories.items():
            if m_name == name:
                return mem

        return None

    def memory_containing(self, addr):
        """
        Finds the memory that contains the given address

        :param addr:  Address to find memory for
        :ret (memory, or None):
        """
        for _, mem in self.memories.items():
            # pylint: disable=chained-comparison
            if addr >= mem.base_addr and addr < (mem.base_addr + mem.size):
                return mem
        return None

    def prepare_and_validate(self):
        """
        Prepares the config for use and validates required entries are
        present.
        """
        self.resolve_intercept_bp_addrs()

        valid = True
        # Validate Memories
        for mem in self.memories.values():
            if not mem.is_valid():
                hal_log.error("Config: %s", mem)
                valid = False

        # Validate Intercepts
        if len(self.intercepts) == 0:
            hal_log.warning("Intercepts is Empty")
        bp_addrs = {}
        del_inters = []
        for inter in self.intercepts:
            if (
                self.machine.arch == "cortex-m3"
                and inter.watchpoint is False
                and inter.bp_addr is not None
            ):
                inter.bp_addr &= 0xFFFFFFFE  # Clear thumb bit so BP is on right address

            if inter.is_valid():
                if inter.bp_addr in bp_addrs:
                    hal_log.warning(
                        "Duplicate Intercept:\n\tOld: %s\n\tNew: %s",
                        bp_addrs[inter.bp_addr],
                        inter,
                    )
                    del_inters.append(bp_addrs[inter.bp_addr])
                bp_addrs[inter.bp_addr] = inter
            else:
                hal_log.error("Config: %s", inter)
                valid = False

        # Remove duplicate intercepts
        for inter in del_inters:
            self.intercepts.remove(inter)

        valid &= self.validate_cortexm_entry_and_sp()

        return valid

    def validate_cortexm_entry_and_sp(self):
        """
        validates that cortex-m3 devices have an entry point and initial sp value.
        If not tries to get them from the memory at address 0
        """
        if self.machine.arch == "cortex-m3":
            if self.machine.entry_addr is None or self.machine.init_sp is None:
                file_found = False
                entry = None
                stack_pointer = None
                for mem in self.memories.values():
                    if mem.base_addr == 0 and mem.file is not None:
                        with open(mem.file, "rb") as bin_file:
                            stack_pointer, entry = unpack("<II", bin_file.read(8))
                            file_found = True
                            break
                if not file_found:
                    hal_log.error(
                        "No Entry Addr or initial SP set. Either specify or provide a file"
                        " at base addr 0x00000000 for cortex-m3"
                    )
                    return False
                if self.machine.entry_addr is None:
                    self.machine.entry_addr = entry
                if self.machine.init_sp is None:
                    self.machine.init_sp = stack_pointer
        return True

    def initialize_target(self, qemu_target):
        """
        Initializes the qemu target after it is created

        :param qemu_target: The qemu_target
        """
        log.debug("Initializing Target")
        if self.elf_program is not None:
            log.debug("Calling ELF Initialize")
            self.elf_program.initialize(qemu_target)
        elif self.machine.entry_addr is not None:
            log.debug("Setting PC to Entry point 0x%0x", self.machine.entry_addr)
            qemu_target.regs.pc = self.machine.entry_addr
