"""
Commander Role
"""
from typing import List
from math import floor

# pylint: disable-next=relative-beyond-top-level)
from ...entities.data_types import Ballot, Proposal

# pylint: disable-next=relative-beyond-top-level)
from ...entities.messages_types import Preempted, Accept, Decided, Decision

# pylint: disable-next=relative-beyond-top-level)
from ...constants import ACCEPT_RETRANSMIT
from . import Role
from ..node import Node


class Commander(Role):
    """
    The leader creates a commander role for each slot where it has an active proposal. Like a scout, a
    commander sends and re-sends Accept messages and waits for a majority of acceptors to reply with
    Accepted or for news of its preemption. When a proposal is accepted, the commander broadcasts a
    Decision message to all nodes. It responds to the leader with Decided or Preempted
    """

    # pylint: disable-next=too-many-arguments
    def __init__(
        self, node: Node, ballot_num: Ballot, slot: int, proposal: Proposal, peers: List
    ) -> None:
        """
        Creates an instance of the Commander Role
        """
        super().__init__(node)
        self.ballot_num = ballot_num
        self.slot = slot
        self.proposal = proposal
        self.acceptors = set([])
        self.peers = peers
        self.quorum = floor(len(peers) / 2 + 1)

    def start(self):
        """
        Starts the Commander role
        """
        self.node.send(
            set(self.peers) - self.acceptors,
            Accept(slot=self.slot, ballot_num=self.ballot_num, proposal=self.proposal),
        )
        self.set_timer(ACCEPT_RETRANSMIT, self.start)

    def finished(self, ballot_num: Ballot, preempted: bool):
        """
        Handles finished process and stops the node before unregistering it
        """
        if preempted:
            self.node.send(
                [self.node.address], Preempted(slot=self.slot, preempted_by=ballot_num)
            )
        else:
            self.node.send([self.node.address], Decided(slot=self.slot))
        self.stop()

    def do_accepted(self, sender, slot: int, ballot_num: Ballot):
        """
        Handles Accepted message types.
        """
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
