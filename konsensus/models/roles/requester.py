from typing import Callable
from itertools import count
from . import Role
from ..node import Node
from konsensus.entities.messages_types import Invoke
from konsensus.constants import INVOKE_RETRANSMIT


class Requester(Role):
    """
    The requester role manages a request to the distributed state machine. 
    The role class simply sends Invoke messages to the local replica until it receives a corresponding Invoked.
    """

    client_ids = count(start=100000)

    def __init__(self, node: Node, n, callback: Callable) -> None:
        super().__init__(node)
        self.client_id = next(self.client_ids)
        self.n = n
        self.output = None
        self.callback = callback

    def start(self):
        self.node.send([self.node.address], Invoke(
            caller=self.node.address, client_id=self.client_id, input_value=self.n))
        self.invoke_timer = self.set_timer(INVOKE_RETRANSMIT, self.start)

    def do_invoked(self, sender, client_id, output):
        if client_id != self.client_id:
            return
        self.logger.debug(f"received output {output}")
        self.invoke_timer.cancel()
        self.callback(output)
        self.stop()
