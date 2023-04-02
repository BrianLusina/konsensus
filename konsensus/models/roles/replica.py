"""
Replica Role
"""
from typing import Dict, Callable, List
# pylint: disable-next=relative-beyond-top-level)
from ...entities.data_types import Proposal
# pylint: disable-next=relative-beyond-top-level)
from ...entities.messages_types import Propose, Invoked, Welcome
# pylint: disable-next=relative-beyond-top-level)
from ...constants import LEADER_TIMEOUT
from . import Role
from ..node import Node


# pylint: disable-next=too-many-instance-attributes
class Replica(Role):
    """
    Replica has the following roles to play
    - Making new proposals;
    - Invoking the local state machine when proposals are decided;
    - Tracking the current leader; and
    - Adding newly started nodes to the cluster.
    """

    # pylint: disable-next=missing-function-docstring
    # pylint: disable-next=too-many-arguments
    def __init__(
            self,
            node: Node,
            execute_fn: Callable,
            state,
            slot,
            decisions: Dict[int, Proposal],
            peers: List,
    ) -> None:
        super().__init__(node)
        self.execute_fn = execute_fn
        self.state = state
        self.slot = slot
        self.decisions = decisions
        self.peers = peers
        self.proposals: Dict[int, Proposal] = {}
        self.next_slot: int = slot
        self.latest_leader = None
        self.latest_leader_timeout = None

    # pylint: disable-next=missing-function-docstring)
    def do_invoke(self, sender, caller, client_id, input_value):
        self.logger.info(
            f"Invoke received. Caller: {caller}, client_id: {client_id}, input_value: {input_value} sender {sender}")
        # making proposals
        proposal = Proposal(caller=caller, client_id=client_id, input=input_value)
        slot = next((s for s, p in self.proposals.items() if p == proposal), None)
        # propose or re-propose if this proposal already has a slot
        self.propose(proposal, slot)

    def propose(self, proposal: Proposal, slot=None):
        """Send (or resend if slot is specified) a proposal to the leader"""
        if not slot:
            slot, self.next_slot = self.next_slot, self.next_slot + 1
        self.proposals[slot] = proposal
        # find a leader we think is working - either the latest we know of, or
        # ourselves(which may trigger a scout to make use the leader)
        leader = self.latest_leader or self.node.address
        self.logger.info(f"proposing {proposal} at slot {slot} to leader {leader}")
        self.node.send([leader], Propose(slot=slot, proposal=proposal))

    # pylint: disable-next=missing-function-docstring)
    def do_decision(self, sender, slot, proposal: Proposal):
        self.logger.info(f"Decision received. Slot: {slot}, proposal: {proposal} from sender {sender}")

        # handling deciding proposals
        assert not self.decisions.get(
            self.slot, None
        ), "next slot to commit is already decided"

        if slot in self.decisions:
            assert (
                    self.decisions[slot] == Proposal
            ), f"slot {slot} already decided with {self.decisions[slot]}"
            return

        self.decisions[slot] = proposal
        self.next_slot = max(self.next_slot, slot + 1)

        # re-propose our proposal in a new slot if it lost its slot and was not a no-op
        our_proposal = self.proposals.get(slot)
        if (
                our_proposal is not None
                and our_proposal != proposal
                and our_proposal.caller
        ):
            self.propose(our_proposal)

        # execute any pending decided proposals
        while True:
            commit_proposal = self.decisions.get(self.slot)
            if not commit_proposal:
                break  # not yet decided
            commit_slot, self.slot = self.slot, self.slot + 1

            self.commit(commit_slot, commit_proposal)

    def commit(self, slot: int, proposal: Proposal):
        """Actually commit a proposal that is decided and in sequence"""
        decided_proposals = [p for s, p in self.decisions.items() if s < slot]
        if proposal in decided_proposals:
            self.logger.info(
                f"not committing duplicate proposal {proposal}, slot {slot}"
            )
            return  # duplicate

        self.logger.info(f"committing {proposal} at slot {slot}")
        if proposal.caller is not None:
            # perform a client operation
            self.state, output = self.execute_fn(self.state, proposal.input)
            self.node.send(
                [proposal.caller], Invoked(client_id=proposal.client_id, output=output)
            )

    # pylint: disable-next=missing-function-docstring)
    def do_adopted(self, sender, ballot_num, accepted_proposals):
        self.logger.info(
            f"Adopted ballot_num {ballot_num} & accepted proposalsL {accepted_proposals} from sender {sender}")
        # tracking the leader
        self.latest_leader = self.node.address
        self.leader_alive()

    # pylint: disable-next=missing-function-docstring)
    def do_accepting(self, sender, leader):
        self.logger.info(f"Accepting from sender {sender}")
        self.latest_leader = leader
        self.leader_alive()

    # pylint: disable-next=missing-function-docstring)
    def do_active(self, sender):
        if sender != self.latest_leader:
            return
        self.leader_alive()

    # pylint: disable-next=missing-function-docstring)
    def leader_alive(self):
        if self.latest_leader_timeout:
            self.latest_leader_timeout.cancel()

        # pylint: disable-next=missing-function-docstring)
        def reset_leader():
            idx = self.peers.index(self.latest_leader)
            self.latest_leader = self.peers[(idx + 1) % len(self.peers)]
            self.logger.debug(
                f"leader timed out; trying the next one, {self.latest_leader}"
            )

        self.latest_leader_timeout = self.set_timer(LEADER_TIMEOUT, reset_leader)

    # pylint: disable-next=missing-function-docstring)
    def do_join(self, sender):
        if sender in self.peers:
            # adding new cluster members
            self.node.send(
                [sender],
                Welcome(state=self.state, slot=self.slot, decisions=self.decisions),
            )
