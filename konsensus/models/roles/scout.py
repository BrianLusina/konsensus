"""
Scout Node role
"""
from typing import List, Dict, Tuple
from konsensus.entities.data_types import Ballot, Proposal
from konsensus.entities.messages_types import Prepare, Adopted, Preempted
from konsensus.constants import PREPARE_RETRANSMIT
from . import Role
from ..node import Node


class Scout(Role):
    """
    The leader creates a scout role when it wants to become active, in response to receiving a Propose when it is
    inactive. The scout sends(and re-sends, if necessary) a Prepare message, and collects Promise responses until it
    has heard from a majority of its peers or until it has been preempted. It communicates back to the leader with
    Adopted or Preempted, respectively.
    """

    def __init__(self, node: Node, ballot_num: Ballot, peers: List) -> None:
        super().__init__(node)
        self.ballot_num = ballot_num
        self.accepted_proposals: Dict[int, Tuple[Ballot, Proposal]] = {}
        self.acceptors = set([])
        self.peers = peers
        self.quorum = len(peers) / 2 + 1
        self.retransmit_timer = None

    # pylint: disable-next=missing-function-docstring
    def start(self):
        self.logger.info("scout starting")
        self.send_prepare()

    # pylint: disable-next=missing-function-docstring
    def send_prepare(self):
        self.node.send(self.peers, Prepare(ballot_num=self.ballot_num))
        self.retransmit_timer = self.set_timer(PREPARE_RETRANSMIT, self.send_prepare)

    # pylint: disable-next=missing-function-docstring
    def update_accepted(self, accepted_proposals: Dict[int, Tuple[Ballot, Proposal]]):
        acc = self.accepted_proposals
        for slot, (ballot_num, proposal) in accepted_proposals.items():
            if slot not in acc or acc[slot][0] < ballot_num:
                acc[slot] = (ballot_num, proposal)

    # pylint: disable-next=missing-function-docstring
    def do_promise(
            self, sender, ballot_num: Ballot, accepted_proposals: Dict[int, Tuple[Ballot, Proposal]]
    ):
        if ballot_num == self.ballot_num:
            self.logger.info(f"got matching promise; need {self.quorum}")
            self.update_accepted(accepted_proposals)
            self.acceptors.add(sender)
            if len(self.acceptors) >= self.quorum:
                # strip ballot numbers from self.accepted_proposals, now that it represents a majority
                accepted_proposals = dict(
                    (s, p) for s, (b, p) in self.accepted_proposals.items()
                )
                # We're adopted; note that this does not mean that no other leader is active. Any such
                # conflicts will be handled by the commanders
                self.node.send(
                    [self.node.address],
                    Adopted(
                        ballot_num=ballot_num, accepted_proposals=accepted_proposals
                    ),
                )
                self.stop()

        else:
            # this acceptor has promised another leader a higher ballot number, so we have lost
            self.node.send(
                [self.node.address], Preempted(slot=None, preempted_by=ballot_num)
            )
            self.stop()
