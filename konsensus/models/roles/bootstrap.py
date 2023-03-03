from typing import List, Callable
from itertools import cycle
from . import Role
from .replica import Replica
from .acceptor import Acceptor
from .leader import Leader
from .commander import Commander
from .scout import Scout
from ..node import Node
from konsensus.entities.messages_types import Join
from konsensus.constants import JOIN_RETRANSMIT


class Bootstrap(Role):
    """
    When a node joins the cluster, it must determine the current cluster state before it can participate. 
    The bootstrap role handles this by sending Join messages to each peer in turn until it receives a Welcome. 
    """
    def __init__(self, node: Node, peers: List, execute_fn: Callable, replica: Replica=Replica, acceptor: Acceptor=Acceptor, leader: Leader=Leader, commander: Commander=Commander, scout: Scout=Scout) -> None:
        super().__init__(node)
        self.execute_fn = execute_fn
        self.peers = peers
        self.peers_cycle = cycle(peers)
        self.replica = replica
        self.acceptor = acceptor
        self.leader = leader
        self.commander = commander
        self.scout = scout
    
    def start(self):
        self.join()
    
    def join(self):
        self.node.send([next(self.peers_cycle)], Join())
        self.set_timer(JOIN_RETRANSMIT, self.join)
    
    def do_welcome(self, sender, state, slot: int, decisions):
        self.acceptor(self.node)
        self.replica(self.node, execute_fn=self.execute_fn, peers=self.peers, state=self.state, slot=self.slot, decision=self.decisions)
        self.leader(self.node, peers=self.peers, commander=self.commander, scout=self.scout).start()
        self.stop
