from typing import Dict, List
from . import Role
from .commander import Commander
from .scout import Scout
from ..node import Node
from konsensus.entities.data_types import Ballot, Proposal
from konsensus.entities.messages_types import Active
from konsensus.constants import LEADER_TIMEOUT


class Leader(Role):
    """
    The leader's primary task is to take Propose messages requesting new ballots and produce decisions.
    A leader is "active" when it has successfully carried out the Prepare/Promise portion of the protocol.
    An active leader can immediately send an Accept message in response to a Propose.

    In keeping with the class-per-role model, the leader delegates to the scout and commander roles to carry out each portion of the protocol.
    """

    def __init__(
        self, node: Node, peers: List, commander=Commander, scout=Scout
    ) -> None:
        super().__init__(node)
        self.ballot_num = Ballot(0, node.address)
        self.active = False
        self.proposals: Dict[int, Proposal] = {}
        self.commander = commander
        self.scout = scout
        self.scouting = False
        self.peers = peers

    def start(self):
        # remind others we are active before LEADER_TIMEOUT expires
        def active():
            if self.active:
                self.node.send(self.peers, Active())
            self.set_timer(LEADER_TIMEOUT / 2.0, active)

        active()

    def spawn_scout(self):
        assert not self.scouting
        self.scouting = True
        self.scout(self.node, self.ballot_num, self.peers).start()

    def do_adopted(
        self, sender, ballot_num: Ballot, accepted_proposals: Dict[int, Proposal]
    ):
        self.scouting = False
        self.proposals.update(accepted_proposals)
        # note that we don't re-spawn commanders here; if there are undecided proposals, the replicas will re-propose
        self.logger.info("leader becoming active")
        self.active = True

    def spawn_commander(self, ballot_num: Ballot, slot: int):
        proposal = self.proposals[slot]
        self.commander(self.node, ballot_num, slot, proposal, self.peers).start()

    def do_preempted(self, sender, slot, preempted_by):
        if not slot:  # from the scout
            self.scouting = False
        self.logger.info(f"leader preempted by {preempted_by.leader}")
        self.active = False
        self.ballot_num = Ballot(
            (preempted_by or self.ballot_num).n + 1, self.ballot_num.leader
        )

    def do_propose(self, sender, slot: int, proposal: Proposal):
        if slot not in self.proposals:
            if self.active:
                self.proposals[slot] = proposal
                self.logger.info(f"spawning commander for slot {slot}")
                self.spawn_commander(self.ballot_num, slot)
            else:
                if not self.scouting:
                    self.logger.info("got PROPOSE when not active - scouting")
                    self.spawn_scout()
                else:
                    self.logger.info("got PROPOSE while scouting; ignored")
        else:
            self.logger.info("got PROPOSE for a slot already being proposed")
