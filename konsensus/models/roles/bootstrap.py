"""
Bootstrap role
"""
from typing import List, Callable
from itertools import cycle
# pylint: disable-next=relative-beyond-top-level)
from ...entities.messages_types import Join
# pylint: disable-next=relative-beyond-top-level)
from ...constants import JOIN_RETRANSMIT
from . import Role
from .replica import Replica
from .acceptor import Acceptor
from .leader import Leader
from .commander import Commander
from .scout import Scout
from ..node import Node


# pylint: disable-next=too-many-instance-attributes
class Bootstrap(Role):
    """
    When a node joins the cluster, it must determine the current cluster state before it can participate.
    The bootstrap role handles this by sending Join messages to each peer in turn until it receives a Welcome.
    """

    # pylint: disable-next=missing-function-docstring
    # pylint: disable-next=too-many-arguments
    def __init__(
            self,
            node: Node,
            peers: List,
            execute_fn: Callable,
            replica: Replica = Replica,
            acceptor: Acceptor = Acceptor,
            leader: Leader = Leader,
            commander: Commander = Commander,
            scout: Scout = Scout,
    ) -> None:
        super().__init__(node)
        self.execute_fn = execute_fn
        self.peers = peers
        self.peers_cycle = cycle(peers)
        self.replica = replica
        self.acceptor = acceptor
        self.leader = leader
        self.commander = commander
        self.scout = scout

    # pylint: disable-next=missing-function-docstring
    def start(self):
        self.join()

    # pylint: disable-next=missing-function-docstring
    def join(self):
        self.node.send([next(self.peers_cycle)], Join())
        self.set_timer(JOIN_RETRANSMIT, self.join)

    # pylint: disable-next=missing-function-docstring
    def do_welcome(self, sender, state, slot: int, decisions):
        self.logger.info(f"Welcome received from {sender}")
        self.acceptor(self.node)
        self.replica(
            self.node,
            execute_fn=self.execute_fn,
            peers=self.peers,
            state=state,
            slot=slot,
            decisions=decisions,
        )
        self.leader(
            self.node, peers=self.peers, commander=self.commander, scout=self.scout
        ).start()
        self.stop()
