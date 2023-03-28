from typing import List, Callable, Optional
import unittest
import itertools
from konsensus.network import Network
from konsensus.models.node import Node
from konsensus.models.roles.seed import Seed
from konsensus.models.roles.requester import Requester
from konsensus.models.roles.bootstrap import Bootstrap
from konsensus.models.roles.leader import Leader


class IntegrationTestCases(unittest.TestCase):
    def setUp(self) -> None:
        self.network = Network(1234)
        self.addresses = ("node-%d" % d for d in itertools.count())
        self.nodes: List[Node] = []
        self.events = []

    def tearDown(self) -> None:
        if self.events:
            self.fail(f"unhandled events: {self.events}")

    def event(self, name):
        self.events.append((self.network.now, name))

    def add_node(self, address: str) -> Node:
        node = self.network.new_node(address=address)
        self.nodes.append(node)
        return node

    def assert_event(self, time, name, fuzz=0):
        for idx, event in enumerate(self.events):
            if event[1] == name and time - fuzz <= event[0] <= time + fuzz:
                self.events.pop(idx)
                return
        self.fail(f"event {name} not found at or around time {time}; events: {self.events}")

    def setup_network(self, count: int, execute_fn: Optional[Callable] = None) -> List[Node]:
        def add(state, input_):
            state += input_
            return state, state

        execute_fn = execute_fn or add
        peers = ["N%d" % n for n in range(count)]
        nodes = [self.add_node(p) for p in peers]
        Seed(nodes[0], initial_state=0, peers=peers, execute_fn=execute_fn)

        for node in nodes[1:]:
            bootstrap = Bootstrap(node, execute_fn=execute_fn, peers=peers)
            bootstrap.start()

        return nodes

    def kill(self, node: Node):
        node.logger.warning("KILLED BY TESTS")
        del self.network.nodes[node.address]

    def test_two_requests(self):
        """Full run with non-overlapping requests succeeds"""
        nodes = self.setup_network(5)

        def request_done(output):
            self.event(f"request done: {output}")

        def make_request(n, node: Node):
            self.event(f"request: {n}")
            req = Requester(node, n, request_done)
            req.start()

        for time, callback in [
            (1.0, lambda: make_request(5, nodes[1])),
            (5.0, lambda: make_request(6, nodes[2])),
            (10.0, self.network.stop),
        ]:
            self.network.set_timer(None, time, callback)

        self.network.run()
        self.assert_event(1001.0, "request: 5")
        self.assert_event(1002.0, "request done: 5", fuzz=1)
        self.assert_event(1005.0, "request: 6")
        self.assert_event(1005.0, "request done: 11", fuzz=1)

    def test_parallel_requests(self):
        """Full run with parallel requests succeed"""
        N = 10
        nodes = self.setup_network(5)
        results = []
        for n in range(1, N + 1):
            requester = Requester(nodes[n % 4], n, results.append)
            self.network.set_timer(None, 1.0, requester.start)

        self.network.set_timer(None, 10.0, self.network.stop)
        self.network.run()
        self.assertEqual((len(results), results and max(results)), (N, N * (N + 1) / 2), f"got {results}")

    def test_failed_nodes(self):
        """Full run with requests and some nodes dying midway through succeeds"""
        N = 10
        nodes = self.setup_network(7)
        results = []
        for n in range(1, N + 1):
            requester = Requester(nodes[n % 3], n, results.append)
            self.network.set_timer(None, n + 1, requester.start)

        # kill nodes 3 and 4 at N/2 seconds
        self.network.set_timer(None, N / 2 - 1, lambda: self.kill(nodes[3]))
        self.network.set_timer(None, N / 2, lambda: self.kill(nodes[4]))

        self.network.set_timer(None, N * 3.0, self.network.stop)

        self.network.run()
        self.assertEqual((len(results), results and max(results)), (N, N * (N + 1) / 2), f"got {results}")

    def test_failed_leader(self):
        """Full run with requests and a dying leader succeeds"""
        N = 10

        # use a bit-setting function so that we can easily ignore requests made buy the failed node
        def identity(state, input_):
            return state, input_

        nodes = self.setup_network(7, execute_fn=identity)
        results = []

        for n in range(1, N + 1):
            requester = Requester(nodes[n % 6], n, results.append)
            self.network.set_timer(None, n + 1, requester.start)

        # kill the leader node at N/2 seconds (it should be stable by then). Some Requester roles were attached to this
        # node, so we fake success of those requests since we don't know what state they are in right now.
        def is_leader(node):
            try:
                leader_role = [c for c in node.roles if isinstance(c, Leader)][0]
                return leader_role.active
            except IndexError:
                return False

        def kill_leader():
            active_leader_nodes = [n for n in nodes if is_leader(n)]
            if active_leader_nodes:
                active_leader = active_leader_nodes[0]
                active_idx = nodes.index(active_leader)

                # append the N's that this node was requesting
                for n in range(1, N + 1):
                    if n % 6 == active_idx:
                        results.append(n)
                self.kill(active_leader)

        self.network.set_timer(None, N / 2, kill_leader)
        self.network.set_timer(None, 15, self.network.stop)
        self.network.run()
        self.assertEqual(set(results), set(range(1, N + 1)))


if __name__ == '__main__':
    unittest.main()
