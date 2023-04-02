"""
Leader Role
"""
from typing import Dict, List
# pylint: disable-next=relative-beyond-top-level)
from ...entities.data_types import Ballot, Proposal
# pylint: disable-next=relative-beyond-top-level)
from ...entities.messages_types import Active
# pylint: disable-next=relative-beyond-top-level)
from ...constants import LEADER_TIMEOUT
from . import Role
from .commander import Commander
from .scout import Scout
from ..node import Node


class Leader(Role):
    """
    The leader's primary task is to take Propose messages requesting new ballots and produce decisions.
    A leader is "active" when it has successfully carried out the Prepare/Promise portion of the protocol.
    An active leader can immediately send an Accept message in response to a Propose.

    In keeping with the class-per-role model, the leader delegates to the scout and commander roles to carry out each
    portion of the protocol.
    """

    def __init__(
            self, node: Node, peers: List, commander=Commander, scout=Scout
    ) -> None:
        """
        Creates a new Leader Role instance
        """
        super().__init__(node)
        self.ballot_num = Ballot(0, node.address)
        self.active = False
        self.proposals: Dict[int, Proposal] = {}
        self.commander = commander
        self.scout = scout
        self.scouting = False
        self.peers = peers

    def start(self):
        """
        Starts the leader role
        """

        # remind others we are active before LEADER_TIMEOUT expires
        def active():
            """
            Sets a timeout and sends out an Active message
            """
            if self.active:
                self.node.send(self.peers, Active())
            self.set_timer(LEADER_TIMEOUT / 2.0, active)

        active()

    def spawn_scout(self):
        """
        Spawns a new scout if not scouting
        """
        assert not self.scouting
        self.scouting = True
        self.scout(self.node, self.ballot_num, self.peers).start()

    def do_adopted(
            self, sender, ballot_num: Ballot, accepted_proposals: Dict[int, Proposal]
    ):
        """
        Performs an Adopted action
        """
        self.scouting = False
        self.proposals.update(accepted_proposals)
        # note that we don't re-spawn commanders here; if there are undecided proposals, the replicas will re-propose
        self.logger.info(f"leader becoming active. Sender: {sender}. Ballot: {ballot_num}")
        self.active = True

    def spawn_commander(self, ballot_num: Ballot, slot: int):
        """
        Spawn a new commander
        """
        proposal = self.proposals[slot]
        self.commander(self.node, ballot_num, slot, proposal, self.peers).start()

    def do_preempted(self, sender, slot, preempted_by):
        """
        Performs a Pre-empted command
        """
        if not slot:  # from the scout
            self.scouting = False
        self.logger.info(f"leader preempted by {preempted_by.leader}. Sender: {sender}")
        self.active = False
        self.ballot_num = Ballot(
            (preempted_by or self.ballot_num).n + 1, self.ballot_num.leader
        )

    def do_propose(self, sender, slot: int, proposal: Proposal):
        """
        Sends a proposal
        """
        if slot not in self.proposals:
            if self.active:
                self.proposals[slot] = proposal
                self.logger.info(f"spawning commander for slot {slot} from {sender}")
                self.spawn_commander(self.ballot_num, slot)
            else:
                if not self.scouting:
                    self.logger.info(f"got PROPOSE from {sender} when not active - scouting")
                    self.spawn_scout()
                else:
                    self.logger.info(f"got PROPOSE from {sender} while scouting; ignored")
        else:
            self.logger.info(f"got PROPOSE from {sender} for a slot already being proposed")
