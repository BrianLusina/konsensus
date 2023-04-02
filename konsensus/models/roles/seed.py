"""
Seed Node Role
"""
from typing import List, Callable
# pylint: disable-next=relative-beyond-top-level)
from ...entities.messages_types import Welcome
# pylint: disable-next=relative-beyond-top-level)
from ...constants import JOIN_RETRANSMIT
from . import Role
from ..node import Node
from .bootstrap import Bootstrap


class Seed(Role):
    """
    Network partitions are the most challenging failure case for clustered applications. In a network partition,
    all cluster members remain alive, but communication fails between some members.
    For example, if the network link joining a cluster with nodes in Berlin and Taipei fails, the network is partitioned
    If both parts of a cluster continue to operate during a partition, then re-joining the parts after the network link
    is restored can be challenging.
    In the Multi-Paxos case, the healed network would be hosting two clusters with different decisions for the same slot
    numbers.

    To avoid this outcome, creating a new cluster is a user-specified operation. Exactly one node in the cluster runs
    the seed role, with the others running bootstrap as usual.
    The seed waits until it has received Join messages from a majority of its peers, then sends a Welcome with an
    initial state for the state machine and an empty set of decisions.
    The seed role then stops itself and starts a bootstrap role to join the newly-seeded cluster.

    Seed emulates the Join/Welcome part of the bootstrap/replica interaction
    """

    # pylint: disable-next=too-many-arguments
    def __init__(
            self,
            node: Node,
            initial_state,
            execute_fn: Callable,
            peers: List,
            bootstrap_cls=Bootstrap,
    ) -> None:
        """
        Creates a new instance of the Seed Role.
        """
        super().__init__(node)
        self.initial_state = initial_state
        self.execute_fn = execute_fn
        self.peers = peers
        self.bootstrap_cls = bootstrap_cls
        self.seen_peers = set([])
        self.exit_timer = None

    def do_join(self, sender):
        """
        Handles Join Process. This adds the sender to the already seen peers in the cluster
        """
        self.seen_peers.add(sender)
        if len(self.seen_peers) <= len(self.peers) / 2:
            return

        # cluster is ready - welcome everyone
        self.node.send(
            list(self.seen_peers),
            Welcome(state=self.initial_state, slot=1, decisions={}),
        )

        # stick around for long enough that we don't hear any new JOINs from newly formed cluster
        if self.exit_timer:
            self.exit_timer.cancel()
        self.exit_timer = self.set_timer(JOIN_RETRANSMIT * 2, self.finish)

    def finish(self):
        """
        Finish process bootstraps this node in the cluster that was just seeded.
        """
        # bootstrap this node in the cluster we just seeded
        bootstrap = self.bootstrap_cls(self.node, peers=self.peers, execute_fn=self.execute_fn)
        bootstrap.start()
        self.stop()
