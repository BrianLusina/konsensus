"""
Requester role
"""
from typing import Callable, Optional
from itertools import count
# pylint: disable-next=relative-beyond-top-level)
from ...entities.messages_types import Invoke
# pylint: disable-next=relative-beyond-top-level)
from ...constants import INVOKE_RETRANSMIT
from ..timer import Timer
from . import Role
from ..node import Node


class Requester(Role):
    """
    The requester role manages a request to the distributed state machine.
    The role class simply sends Invoke messages to the local replica until it receives a corresponding Invoked.
    """

    client_ids = count(start=100000)

    # pylint: disable-next=missing-function-docstring
    def __init__(self, node: Node, n, callback: Callable) -> None:
        super().__init__(node)
        self.invoke_timer: Optional[Timer] = None
        self.client_id = next(self.client_ids)
        # pylint: disable-next=invalid-name
        self.n = n
        self.output = None
        self.callback = callback

    # pylint: disable-next=missing-function-docstring
    def start(self):
        self.node.send(
            [self.node.address],
            Invoke(
                caller=self.node.address, client_id=self.client_id, input_value=self.n
            ),
        )
        self.invoke_timer = self.set_timer(INVOKE_RETRANSMIT, self.start)

    # pylint: disable-next=missing-function-docstring
    def do_invoked(self, sender, client_id, output):
        if client_id != self.client_id:
            return
        self.logger.debug(f"received output {output} from sender: {sender}")
        self.invoke_timer.cancel()
        self.callback(output)
        self.stop()
