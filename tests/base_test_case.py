from konsensus.entities.data_types import Ballot, Proposal
from .utils.fake_network import FakeNetwork, FakeNode
import unittest


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.network = FakeNetwork()
        self.node = FakeNode(self.network)

    def tearDown(self):
        if self.node.sent:
            self.fail("extra messages from node: %r" % (self.node.sent,))

    def assertMessage(self, destinations, message):
        got = self.node.sent.pop(0)
        self.assertEqual((sorted(destinations), message), (sorted(got[0]), got[1]))

    def assertNoMessages(self):
        self.assertEqual([], self.node.sent)

    def assertTimers(self, times):
        self.assertEqual(times, self.node.network.get_times())

    def assertUnregistered(self):
        self.assertEqual([], self.node.roles)

    def verifyAcceptedProposals(self, accepted_proposals):
        """Verify that the ``accepted_proposals`` field of a promise is formatted
        as a dictionary mapping slots to (ballot, proposal) tuples."""
        self.assertIsInstance(accepted_proposals, dict)
        for k, v in accepted_proposals.items():
            self.assertIsInstance(k, int)
            self.assertIsInstance(v, tuple)
            self.assertEqual(2, len(v))
            self.assertIsInstance(v[0], Ballot)
            self.assertIsInstance(v[1], Proposal)
