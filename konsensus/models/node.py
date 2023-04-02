"""
Node represents a node on the network
"""
from __future__ import annotations
from typing import List, TYPE_CHECKING
from itertools import count
from functools import partial
import logging

# pylint: disable-next=relative-beyond-top-level
from ..infra.logger import SimTimeLogger

if TYPE_CHECKING:
    from .roles import Role
    from ..network import Network


class Node:
    """
    Represents a node on the network
    Messages that arrive on the node are relayed to all active roles, calling a method named after the message type with
    a do_ prefix.
    These do_ methods receive the message's attributes as keyword arguments for easy access. The Node class also
    provides a send method as a convenience, using functools.partial to supply some arguments to the same methods of
    the Network class
    """

    unique_ids = count()

    # pylint: disable-next=missing-function-docstring
    def __init__(self, network: 'Network', address) -> None:
        self.network = network
        self.address = address or f"N{next(self.unique_ids)}"
        self.logger = SimTimeLogger(
            logging.getLogger(self.address), {"network": self.network}
        )
        self.logger.info("starting")
        self.roles: List["Role"] = []
        self.send = partial(self.network.send, self)

    # pylint: disable-next=missing-function-docstring
    def register(self, role: "Role"):
        self.roles.append(role)

    # pylint: disable-next=missing-function-docstring
    def unregister(self, role: "Role"):
        self.roles.remove(role)

    # pylint: disable-next=missing-function-docstring
    def receive(self, sender, message):
        handler_name = f"do_{type(message).__name__}".lower()

        for comp in self.roles[:]:
            if not hasattr(comp, handler_name):
                continue
            comp.logger.debug(f"received {message} from {sender}")
            handler = getattr(comp, handler_name)
            handler(sender=sender, **message._asdict())
