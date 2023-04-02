"""
Member Model
"""
from typing import Optional
import threading
from queue import Queue
# pylint: disable-next=import-error
from .roles.seed import Seed
# pylint: disable-next=import-error
from .roles.bootstrap import Bootstrap
# pylint: disable-next=import-error
from .roles.requester import Requester
# pylint: disable-next=relative-beyond-top-level
from ..network import Network


class Member:
    """
    Represents a Member object on the cluster.
    The member object adds a bootstrap role to the node if it is joining an existing cluster, or seed if it is creating
    a new cluster. It then runs the protocol (via Network.run) in a separate thread.

    The application interacts with the cluster through the invoke method, which kicks off a proposal for a state
    transition.
    Once that proposal is decided and the state machine runs, invoke returns the machine's output.
    The method uses a simple synchronized Queue to wait for the result from the protocol thread.
    """

    # pylint: disable-next=missing-function-docstring
    # pylint: disable-next=too-many-arguments
    def __init__(
            self,
            state_machine,
            network: Network,
            peers,
            seed=None,
            seed_cls=Seed,
            bootstrap=Bootstrap,
    ) -> None:
        self.thread: Optional[threading.Thread] = None
        self.network = network
        self.node = network.new_node()
        if seed is not None:
            self.startup_role = seed_cls(
                self.node, initial_state=seed, peers=peers, execute_fn=state_machine
            )
        else:
            self.startup_role = bootstrap(
                self.node, execute_fn=state_machine, peers=peers
            )
        self.requester = None

    # pylint: disable-next=missing-function-docstring
    def start(self):
        self.startup_role.start()
        self.thread = threading.Thread(target=self.network.run)
        self.thread.start()

    # pylint: disable-next=missing-function-docstring
    def invoke(self, input_value, request_cls=Requester):
        assert self.requester is None
        queue = Queue()
        self.requester = request_cls(self.node, input_value, queue.put)
        self.requester.start()
        output = queue.get()
        self.requester = None
        return output
