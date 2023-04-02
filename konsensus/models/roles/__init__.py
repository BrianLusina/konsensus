"""
Base Role
"""
from __future__ import annotations
from typing import Callable
from ..node import Node


class Role:
    """Represents roles corresponding to the cluster"""

    # pylint: disable-next=missing-function-docstring)
    def __init__(self, node: "Node") -> None:
        self.node = node
        self.node.register(self)
        self.running = True
        self.logger = node.logger.getChild(type(self).__name__)

    # pylint: disable-next=missing-function-docstring)
    def set_timer(self, seconds: int, callback: Callable):
        return self.node.network.set_timer(
            self.node.address, seconds, lambda: self.running and callback()
        )

    # pylint: disable-next=missing-function-docstring)
    def stop(self):
        self.running = False
        self.node.unregister(self)
