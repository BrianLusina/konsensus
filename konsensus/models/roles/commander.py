from typing import List
from . import Role
from ..node import Node
from konsensus.entities.data_types import Ballot, Proposal
from konsensus.entities.messages_types import Preempted, Accept, Decided, Decision
from konsensus.constants import ACCEPT_RETRANSMIT


class Commander(Role):
    """
    The leader creates a commander role for each slot where it has an active proposal. Like a scout, a 
    commander sends and re-sends Accept messages and waits for a majority of acceptors to reply with 
    Accepted or for news of its preemption. When a proposal is accepted, the commander broadcasts a
    Decision message to all nodes. It responds to the leader with Decided or Preempted
    """

    def __init__(self, node: Node, ballot_num: Ballot, slot: int, proposal: Proposal, peers: List) -> None:
        super().__init__(node)
        self.ballot_num = ballot_num
        self.slot = slot
        self.proposal = proposal
        self.acceptors = set([])
        self.peers = peers
        self.quorum = len(peers) / 2 + 1
    
    def start(self):
        self.node.send(set(self.peers) - self.acceptors, Accept(slot=self.slot, ballot_num=self.ballot_num, proposal=self.proposal))
        self.set_timer(ACCEPT_RETRANSMIT, self.start)
    
    def finished(self, ballot_num: Ballot, preempted: bool):
        if preempted:
            self.node.send([self.node.address], Preempted(slot=self.slot, preempted_by=ballot_num))
        else:
            self.node.send([self.node.address], Decided(slot=self.slot))
        self.stop()
    
    def do_accepted(self, sender, slot: int, ballot_num: Ballot):
        if slot != self.slot:
            return
        if ballot_num == self.ballot_num:
            self.acceptors.add(sender)
            if len(self.acceptors) < self.quorum:
                return
            self.node.send(self.peers, Decision(slot=self.slot, proposal=self.proposal))
            self.finished(ballot_num, False)
        else:
            self.finished(ballot_num, True)
