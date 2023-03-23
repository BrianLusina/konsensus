import unittest
import unittest.mock as mock
from konsensus.network import Network
from konsensus.models.node import Node
from konsensus.models.roles import Role
from konsensus.entities.messages_types import Join


class TestRole(Role):
    join_called = False

    def do_join(self, sender):
        self.join_called = True
        self.kill()


class NetworkTestCases(unittest.TestCase):
    def setUp(self) -> None:
        self.network = Network(1234)

    def kill(self, node: Node):
        del self.network.nodes[node.address]

    def test_communication(self):
        """Node can successfully send a message between instances"""
        sender = self.network.new_node("S")
        receiver = self.network.new_node("R")
        component = TestRole(receiver)
        component.kill = lambda: self.kill(receiver)
        sender.send([receiver.address], Join())
        self.network.run()
        self.failUnless(component.join_called)

    def test_timeout(self):
        """Node's timeouts trigger at the appropriate time"""
        node = self.network.new_node('T')

        cb = mock.Mock(side_effect=lambda: self.kill(node))
        self.network.set_timer(node.address, 0.01, cb)
        self.network.run()
        self.failUnless(cb.called)

    def test_cancel_timeout(self):
        """Node's timeouts do not occur if they are cancelled."""
        node = self.network.new_node('C')

        def fail():
            raise RuntimeError("nooo")

        nonex = self.network.set_timer(node.address, 0.01, fail)

        cb = mock.Mock(side_effect=lambda: self.kill(node))
        self.network.set_timer(node.address, 0.02, cb)
        nonex.cancel()
        self.network.run()
        self.failUnless(cb.called)


if __name__ == '__main__':
    unittest.main()
