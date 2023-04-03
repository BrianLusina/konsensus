import unittest
import unittest.mock as mock
from unittest.mock import patch
import pytest
from konsensus.models.roles.requester import Requester
from konsensus.entities.messages_types import Invoke, Invoked
from konsensus.constants import INVOKE_RETRANSMIT
from tests.base_test_case import BaseTestCase

CLIENT_ID = 999999


class RequesterTestCase(BaseTestCase):

    @pytest.mark.xfail(reason="this will fail do to the failure to mock client ids")
    def setUp(self):
        super().setUp()
        self.callback = mock.Mock(name="callback")

        with patch.object(Requester, "client_ids") as mock_client_ids:
            mock_client_ids.return_value = CLIENT_ID

        self.requester = Requester(self.node, 10, self.callback)
        self.assertEqual(self.requester.client_id, CLIENT_ID)

    @pytest.mark.xfail(reason="this will fail do to the client_id changing.")
    def test_repeatedly_send_invoke_until_receiving_a_match_invoked(self):
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
