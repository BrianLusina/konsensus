from __future__ import annotations
from typing import List
from itertools import count
from functools import partial
import logging
from .roles import Role
from ..infra.logger import SimTimeLogger


class Node:
    """
    Represents a node on the network
    Messages that arrive on the node are relayed to all active roles, calling a method named after the message type with a do_ prefix. 
    These do_ methods receive the message's attributes as keyword arguments for easy access. The Node class also provides a send 
    method as a convenience, using functools.partial to supply some arguments to the same methods of the Network class
    """
    unique_ids = count()

    def __init__(self, network, address) -> None:
        self.network = network
        self.address = address or f'N{self.unique_ids.next()}'
        self.logger = SimTimeLogger(logging.getLogger(self.address), {'network': self.network})
        self.logger.info('starting')
        self.roles: List[Role] = []
        self.send = partial(self.network.send, self)    

    def register(self, role: Role):
        self.roles.append(role)
    
    def unregister(self, role: Role):
        self.roles.remove(role)
    
    def receive(self, sender, message):
        handler_name = 'do_%s' % type(message).__name__

        for comp in self.roles[:]:
            if not hasattr(comp, handler_name):
                continue
            comp.logger.debug(f"received {message} from {sender}")
            fn = getattr(comp, handler_name)
            fn(sender=sender, **message._asdict())
