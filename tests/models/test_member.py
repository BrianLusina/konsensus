import unittest
import unittest.mock as mock
from konsensus.models.node import Node
from konsensus.models.roles.bootstrap import Bootstrap
from konsensus.models.roles.seed import Seed
from konsensus.models.member import Member
from tests.utils.fake_request import FakeRequest
from tests.utils.fake_network import FakeNetwork


class MemberTestCases(unittest.TestCase):
    def setUp(self):
        self.MockNode = mock.create_autospec(Node)
        self.MockBootstrap = mock.create_autospec(Bootstrap)
        self.MockSeed = mock.create_autospec(Seed)
        self.network = FakeNetwork()
        self.state_machine = mock.Mock(name="state_machine")
        self.cls_args = dict(bootstrap=self.MockBootstrap, seed_cls=self.MockSeed)

    def test_no_seed(self):
        """With no seed, the Member constructor builds a Bootstrap"""
        _ = Member(self.state_machine, network=self.network, peers=['p1', 'p2'], **self.cls_args)
        self.failIf(self.MockSeed.called)
        self.MockBootstrap.assert_called_with(
            self.network.node, execute_fn=self.state_machine, peers=["p1", "p2"]
        )

    def test_member(self):
        """With a seed, the Member constructor builds a node and a ClusterSeed"""
        _ = Member(self.state_machine, network=self.network, peers=['p1', 'p2'], seed=44, **self.cls_args)
        self.failIf(self.MockBootstrap.called)
        self.MockSeed.assert_called_with(
            self.network.node, initial_state=44, execute_fn=self.state_machine, peers=["p1", "p2"]
        )

    def test_start(self):
        """Member.start starts the role and node in self.thread"""
        member = Member(self.state_machine, network=self.network, peers=['p1', 'p2'], **self.cls_args)
        member.start()
        member.thread.join()
        member.startup_role.start.assert_called_once_with()
        self.failUnless(self.network.ran)

    def test_invoke(self):
        """Member.invoke makes a new request, starts it & waits for its callback to be called"""
        member = Member(self.state_machine, network=self.network, peers=['p1', 'p2'], **self.cls_args)
        result = member.invoke("ROTATE", request_cls=FakeRequest)
        self.assertEqual(member.requester, None)
        self.assertEqual(result, ("ROTATED", member.node, "ROTATE"))


if __name__ == '__main__':
    unittest.main()
