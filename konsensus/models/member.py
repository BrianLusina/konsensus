import threading
from queue import Queue
from .roles.seed import Seed
from .roles.bootstrap import Bootstrap
from .roles.requester import Requester
from ..network import Network


class Member:
    """
    Represents a Member object on the cluster.
    The member object adds a bootstrap role to the node if it is joining an existing cluster, or seed if it is creating a new cluster.
    It then runs the protocol (via Network.run) in a separate thread.

    The application interacts with the cluster through the invoke method, which kicks off a proposal for a state transition.
    Once that proposal is decided and the state machine runs, invoke returns the machine's output.
    The method uses a simple synchronized Queue to wait for the result from the protocol thread.
    """

    def __init__(
        self,
        state_machine,
        network: Network,
        peers,
        seed=None,
        seed_cls=Seed,
        bootstrap=Bootstrap,
    ) -> None:
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

    def start(self):
        self.startup_role.start()
        self.thread = threading.Thread(target=self.network.run)
        self.thread.start()

    def invoke(self, input_value, request_cls=Requester):
        assert self.requester is None
        q = Queue()
        self.requester = request_cls(self.node, input_value, q.put)
        self.requester.start()
        output = q.get()
        self.requester = None
        return output
