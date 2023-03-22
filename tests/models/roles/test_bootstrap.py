import unittest
import unittest.mock as mock
from konsensus.models.roles.acceptor import Acceptor
from konsensus.models.roles.replica import Replica
from konsensus.models.roles.leader import Leader
from konsensus.models.roles.commander import Commander
from konsensus.models.roles.scout import Scout
from konsensus.models.roles.bootstrap import Bootstrap
from konsensus.constants import JOIN_RETRANSMIT
from konsensus.entities.messages_types import Join, Welcome
from tests.base_test_case import BaseTestCase


class BootstrapTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.cb_args = None
        self.execute_fn = mock.Mock()
        self.replica = mock.Mock(spec=Replica)
        self.acceptor = mock.Mock(spec=Acceptor)
        self.leader = mock.Mock(spec=Leader)
        self.commander = mock.Mock(spec=Commander)
        self.scout = mock.Mock(spec=Scout)
        self.bootstrap = Bootstrap(self.node, ['p1', 'p2', 'p3'], self.execute_fn, replica=self.replica,
                                   acceptor=self.acceptor, leader=self.leader, commander=self.commander,
                                   scout=self.scout
                                   )

    def test_transit(self):
        """After start(), the bootstrap sends JOIN to each node in sequence until hearing WELCOME"""
        self.bootstrap.start()

        for recip in 'p1', 'p2', 'p3', 'p1':
            self.assertMessage([recip], Join())
            self.network.tick(JOIN_RETRANSMIT)
        self.assertMessage(['p2'], Join())

        self.node.fake_message(Welcome(state='st', slot='sl', decisions={}))
        self.acceptor.assert_called_with(self.node)
        self.replica.assert_called_with(self.node, execute_fn=self.execute_fn, decisions={}, state="st", slot="sl",
                                        peers=['p1', 'p2', 'p3'])
        self.leader.assert_called_with(self.node, peers=['p1', 'p2', 'p3'], commander=self.commander, scout=self.scout)
        self.leader().start.assert_called_with()
        self.assertTimers([])
        self.assertUnregistered()


if __name__ == '__main__':
    unittest.main()
