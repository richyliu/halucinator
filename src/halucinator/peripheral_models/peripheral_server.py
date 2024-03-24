# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""
Peripheral Server that enables external devices to send and receive events
from HALucinator over ZMQ
"""

import logging
from functools import wraps
import yaml
import zmq

log = logging.getLogger(__name__)

# pylint: disable=global-statement

__RX_HANDLERS__ = {}
__RX_CONTEXT__ = zmq.Context()
__TX_CONTEXT__ = zmq.Context()
__STOP_SERVER = False
__RX_SOCKET__ = None
__TX_SOCKET__ = None

__PROCESS = None
__QEMU = None

OUTPUT_DIRECTORY = None


def peripheral_model(cls):
    """
    Decorator which registers classes as peripheral models
    """
    methods = [
        getattr(cls, x) for x in dir(cls) if hasattr(getattr(cls, x), "is_rx_handler")
    ]
    for method in methods:
        key = f"Peripheral.{cls.__name__}.{method.__name__}"
        log.info("Adding method: %s", key)
        __RX_HANDLERS__[key] = (cls, method)
        if __RX_SOCKET__ is not None:
            log.info("Subscribing to: %s", key)
            __RX_SOCKET__.setsockopt(zmq.SUBSCRIBE, bytes(key))

    return cls


def tx_msg(funct):
    """
    This is a decorator that sends output of the wrapped function as
    a tagged msg.  The tag is the class_name.func_name
    """

    @wraps(funct)
    def tx_msg_decorator(model_cls, *args):
        """
        Sends a message using the class.funct as topic
        data is a yaml encoded of the calling model_cls.funct
        """
        data = funct(model_cls, *args)
        topic = f"Peripheral.{model_cls.__name__}.{funct.__name__}"
        msg = encode_zmq_msg(topic, data)
        log.info("Sending: %s", msg)
        __TX_SOCKET__.send_string(msg)

    return tx_msg_decorator


def reg_rx_handler(funct):
    """
    This is a decorator that registers a function to handle a specific
    type of message
    """
    funct.is_rx_handler = True
    return funct


def encode_zmq_msg(topic, msg):
    """
    Encodes a message sent over a zmq

    :param topic: Str of topic to send
    :param msg:  (Data that can be dump to yaml)
    """
    data_yaml = yaml.safe_dump(msg)
    return f"{topic} {data_yaml}"


def decode_zmq_msg(msg):
    """
    Decodes a message sent over a zmq socket
    returns (topic, message)
    """
    topic, encoded_msg = str(msg).split(" ", 1)
    decoded_msg = yaml.safe_load(encoded_msg)
    return (topic, decoded_msg)


def start(rx_port=5555, tx_port=5556, qemu=None):
    """
    Initializes zmq sockets
    """
    global __RX_SOCKET__
    global __TX_SOCKET__
    global __QEMU
    global OUTPUT_DIRECTORY

    OUTPUT_DIRECTORY = qemu.avatar.output_directory
    __QEMU = qemu
    log.info("Starting Peripheral Server, In port %i, outport %i", rx_port, tx_port)
    # Setup subscriber
    io2hal_pipe = f"ipc:///tmp/IoServer2Halucinator{rx_port}"
    __RX_SOCKET__ = __RX_CONTEXT__.socket(zmq.SUB)
    __RX_SOCKET__.bind(io2hal_pipe)
    log.debug("Bound to %s", str(io2hal_pipe))

    for topic in list(__RX_HANDLERS__.keys()):
        log.info("Subscribing to: %s", topic)
        __RX_SOCKET__.setsockopt_string(zmq.SUBSCRIBE, topic)

    # Setup Publisher
    hal2io_pipe = f"ipc:///tmp/Halucinator2IoServer{tx_port}"
    __TX_SOCKET__ = __TX_CONTEXT__.socket(zmq.PUB)
    __TX_SOCKET__.bind(hal2io_pipe)
    log.debug("Bound to %s", str(hal2io_pipe))

    # __process = Process(target=run_server).start()


# def trigger_interrupt(num):
#     global __qemu
#     log.info("Sending Interrupt: %s" % num)
#     __qemu.trigger_interrupt(num)


def irq_set_qmp(irq_num=1):
    """
    set `irq_num` interrupt using qmp interface to QEMU
    Should not be used in BP handlers as creates race
    condition that may cause spurious interrupts
    """
    __QEMU.irq_set_qmp(irq_num)


def irq_clear_qmp(irq_num=1):
    """
    clear `irq_num` interrupt using qmp interface to QEMU
    Should not be used in BP handlers as creates race
    condition that may cause spurious interrupts
    """
    __QEMU.irq_clear_qmp(irq_num)


def irq_enable_qmp(irq_num=1):
    """
    Enables `irq_num` using qmp interface to QEMU.
    This enables the interrupt to fire, but does not trigger the interrupt
    Should not be used in BP handlers as creates race
    condition that may cause spurious interrupts
    """
    __QEMU.irq_enable_qmp(irq_num)


def irq_disable_qmp(irq_num=1):
    """
    Disables `irq_num` using qmp interface to QEMU.
    This keeps the interrupt from firing, even if activated(set)
    Should not be used in BP handlers as creates race
    condition that may cause spurious interrupts
    """
    __QEMU.irq_disable_qmp(irq_num)


def irq_set_bp(irq_num=1):
    """
    Set `irq_num` interrupt using gdb interface using memory accesses
    can be used in bp_handlers,
    """
    __QEMU.irq_set_bp(irq_num)


def irq_clear_bp(irq_num):
    """
    Clear `irq_num` interrupt using gdb interface using memory accesses
    can be used in bp_handlers,
    """
    __QEMU.irq_clear_bp(irq_num)


def irq_enable_bp(irq_num):
    """
    Enables `irq_num` using gdb interface (memory accesses) to QEMU.
    This keeps the interrupt from firing, even if activated(set)
    Can be used in BP Hanlders
    """
    __QEMU.irq_enable_bp(irq_num)


def irq_disable_bp(irq_num):
    """
    Disables `irq_num` using gdb interface (memory accesses) to QEMU.
    This keeps the interrupt from firing, even if activated(set)
    Can be used in BP Hanlders
    """
    __QEMU.irq_disable_bp(irq_num)


# def irq_set(irq_num=1, cpu=0):
#     global __QEMU
#     __QEMU.irq_set(irq_num, cpu)

# def irq_clear(self, irq_num=1, cpu=0):
#     global __QEMU
#     __QEMU.irq_clear(irq_num, cpu)

# def irq_pulse(self, irq_num=1, cpu=0):
#     global __QEMU
#     __QEMU.irq_pulse(irq_num, cpu)


def run_server():
    """
    This the main loop for the peripheral server.
    """
    global __STOP_SERVER  # pylint: disable=global-statement

    __STOP_SERVER = False
    __RX_SOCKET__.setsockopt(zmq.SUBSCRIBE, b"")  # pylint: disable=no-member

    poller = zmq.Poller()
    poller.register(__RX_SOCKET__, zmq.POLLIN)
    while not __STOP_SERVER:
        socks = dict(poller.poll(100))
        if __RX_SOCKET__ in socks and socks[__RX_SOCKET__] == zmq.POLLIN:
            string = __RX_SOCKET__.recv_string()
            topic, msg = decode_zmq_msg(string)
            log.info("Got message: Topic %s  Msg: %s", str(topic), str(msg))
            print(f"Got message: Topic {topic}  Msg: {msg}")
            if topic.startswith("Peripheral"):
                if topic in __RX_HANDLERS__:
                    _, method = __RX_HANDLERS__[topic]
                    method(msg)
                else:
                    log.error("Unhandled peripheral message type received: %s", topic)

            elif topic.startswith("Interrupt.Trigger"):
                log.info("Triggering Interrupt %s", msg["num"])
                irq_set_qmp(msg["num"])
            elif topic.startswith("Interrupt.Base"):
                log.info("Setting Vector Base Addr %s", msg["num"])
                __QEMU.set_vector_table_base(msg["base"])
            else:
                log.error("Unhandled topic received: %s", topic)
    log.info("Peripheral Server Shutdown Normally")


def stop():
    """
    Stop the Peripheral Server
    """
    global __STOP_SERVER  # pylint: disable=global-statement
    __STOP_SERVER = True
