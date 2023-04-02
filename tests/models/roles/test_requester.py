import unittest
import unittest.mock as mock
from konsensus.models.roles.requester import Requester
from konsensus.entities.messages_types import Invoke, Invoked
from konsensus.constants import INVOKE_RETRANSMIT
from tests.base_test_case import BaseTestCase

CLIENT_ID = 999999


class RequesterTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.callback = mock.Mock(name="callback")
        with mock.patch.object(Requester, "client_ids") as client_ids:
            client_ids = CLIENT_ID
        self.requester = Requester(self.node, 10, self.callback)
        # self.assertEqual(self.requester.client_id, CLIENT_ID)

    def test_function(self):
        """Requester should repeatedly send INVOKE until receiving a matching INVOKED"""
        self.requester.start()
        self.assertMessage(["F999"], Invoke(caller="F999", client_id=CLIENT_ID, input_value=10))
        self.network.tick(INVOKE_RETRANSMIT)
        self.assertMessage(["F999"], Invoke(caller="F999", client_id=CLIENT_ID, input_value=10))

        # non matching
        self.node.fake_message(Invoked(client_id=333, output=22))
        self.network.tick(INVOKE_RETRANSMIT)
        self.assertMessage(["F999"], Invoke(caller="F999", client_id=CLIENT_ID, input_value=10))
        self.failIf(self.callback.called)

        self.node.fake_message(Invoked(client_id=CLIENT_ID, output=20))
        self.callback.assert_called_with(20)
        self.assertUnregistered()


if __name__ == '__main__':
    unittest.main()
