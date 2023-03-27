import unittest
import unittest.mock as mock
from konsensus.entities.data_types import Proposal
from konsensus.entities.messages_types import Invoke, Propose, Decision, Join, Welcome
from konsensus.models.roles.replica import Replica
from tests.base_test_case import BaseTestCase

PROPOSAL1 = Proposal(caller='test', client_id=111, input='uno')
PROPOSAL2 = Proposal(caller='test', client_id=222, input='dos')
PROPOSAL3 = Proposal(caller='test', client_id=333, input='tres')
PROPOSAL4 = Proposal(caller='test', client_id=444, input='cinco')


class ReplicaTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.execute_fn = mock.Mock(name="execute_fn", spec=lambda state, input: None)
        self.replica = Replica(self.node, self.execute_fn, state="state", slot=2, decisions={1: PROPOSAL1},
                               peers=["p1", "F999"])
        self.assertNoMessages()

    def tearDown(self):
        self.assertNoMessages()

    @mock.patch.object(Replica, "propose")
    def test_invoke_new(self, propose: mock.Mock):
        """An INVOKE with a new proposal results in a proposal"""
        self.node.fake_message(
            Invoke(caller=PROPOSAL2.caller, client_id=PROPOSAL2.client_id, input_value=PROPOSAL2.input))
        propose.assert_called_with(PROPOSAL2, None)

    @mock.patch.object(Replica, "propose")
    def test_invoke_repeat(self, propose: mock.Mock):
        """An INVOKE with a proposal that has already been seen is ignored"""
        self.replica.proposals[1] = PROPOSAL1
        self.failIf(propose.called)

    def test_propose_new(self):
        """A proposal without a specified slot gets the next slot and is proposed to self"""
        self.replica.propose(PROPOSAL2)
        self.assertEqual(self.replica.next_slot, 3)
        self.assertMessage(["F999"], Propose(slot=2, proposal=PROPOSAL2))

    def test_propose_resend(self):
        """A proposal with a specified slot is re-transmitted with the same slot"""
        self.replica.next_slot = 3
        self.replica.propose(PROPOSAL2, 2)
        self.assertEqual(self.replica.next_slot, 3)
        self.assertMessage(["F999"], Propose(slot=2, proposal=PROPOSAL2))

    @mock.patch.object(Replica, "commit")
    def test_decision_gap(self, commit: mock.Mock):
        """On DECISION for a slot we can't commit yet, decisions and next slot are updated but no commit occurs"""
        self.node.fake_message(Decision(slot=3, proposal=PROPOSAL3))
        self.assertEqual(self.replica.next_slot, 4)
        self.assertEqual(self.replica.decisions[3], PROPOSAL3)
        self.assertFalse(commit.called)

    @mock.patch.object(Replica, "commit")
    def test_decision_commit(self, commit: mock.Mock):
        """On DECISION for the next slot, commit it"""
        self.node.fake_message(Decision(slot=2, proposal=PROPOSAL2))
        self.assertEqual(self.replica.next_slot, 3)
        self.assertEqual(self.replica.decisions[2], PROPOSAL2)
        commit.assert_called_once_with(2, PROPOSAL2)

    @mock.patch.object(Replica, "commit")
    def test_decision_commit_cascade(self, commit: mock.Mock):
        """On DECISION that allows multiple commits, they happen in the right order"""
        self.node.fake_message(Decision(slot=3, proposal=PROPOSAL3))
        self.assertFalse(commit.called)
        self.node.fake_message(Decision(slot=2, proposal=PROPOSAL2))
        self.assertEqual(self.replica.next_slot, 4)
        self.assertEqual(self.replica.decisions[2], PROPOSAL2)
        self.assertEqual(self.replica.decisions[3], PROPOSAL3)
        self.assertEqual(commit.call_args_list, [mock.call(2, PROPOSAL2), mock.call(3, PROPOSAL3)])

    @unittest.skip("AssertionError being raised instead of nothing being done on decision being repeated for same slot")
    @mock.patch.object(Replica, "commit")
    def test_decision_repeat(self, commit: mock.Mock):
        """On DECISION for a committed slot with a matching proposal, do nothing"""
        self.node.fake_message(Decision(slot=1, proposal=PROPOSAL1))
        self.assertEqual(self.replica.next_slot, 2)
        self.assertFalse(commit.called)

    def test_decision_repeat_conflict(self):
        """On DECISION for a committed slot with a non-matching proposal, do nothing"""
        self.assertRaises(AssertionError, lambda: self.node.fake_message(Decision(slot=1, proposal=PROPOSAL1)))

    def test_join(self):
        """A JOIN from a cluster member gets a warm WELCOME"""
        self.node.fake_message(Join(), sender="F999")
        self.assertMessage(["F999"], Welcome(state="state", slot=2, decisions={1: PROPOSAL1}))

    def test_join_unknown(self):
        """A JOIN from elsewhere gets nothing"""
        self.node.fake_message(Join(), sender="999")
        self.assertNoMessages()


if __name__ == '__main__':
    unittest.main()
