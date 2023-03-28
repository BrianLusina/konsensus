import unittest
import unittest.mock as mock
from konsensus.models.roles.bootstrap import Bootstrap
from konsensus.models.roles.seed import Seed
from konsensus.entities.messages_types import Join, Welcome
from konsensus.constants import JOIN_RETRANSMIT
from tests.base_test_case import BaseTestCase


class SeedTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.bootstrap = mock.Mock(autospec=Bootstrap)
        self.execute_fn = mock.Mock()
        self.seed = Seed(self.node, initial_state="state", peers=["p1", "p2", "p3"], execute_fn=self.execute_fn,
                         bootstrap_cls=self.bootstrap)

    def test_join(self):
        """Seed waits for quorum, then sends a WELCOME in response to every JOIN until 2*JOIN_RETRANSMIT seconds have
        passed with no JOINs"""
        self.node.fake_message(Join(), sender="p1")
        self.assertNoMessages()
        self.node.fake_message(Join(), sender="p3")
        self.assertMessage(["p1", "p3"], Welcome(state="state", slot=1, decisions={}))

        self.network.tick(JOIN_RETRANSMIT)
        self.node.fake_message(Join(), sender="p2")
        self.assertMessage(["p1", "p2", "p3"], Welcome(state="state", slot=1, decisions={}))

        self.network.tick(JOIN_RETRANSMIT * 2)
        self.assertNoMessages()
        self.assertUnregistered()
        self.bootstrap.assert_called_with(self.node, peers=["p1", "p2", "p3"], execute_fn=self.execute_fn)
        self.bootstrap().start.assert_called_with()


if __name__ == '__main__':
    unittest.main()
