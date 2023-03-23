import unittest
import unittest.mock as mock
from konsensus.models.roles.scout import Scout
from konsensus.models.roles.commander import Commander
from konsensus.models.roles.leader import Leader
from konsensus.entities.messages_types import Propose, Preempted, Adopted
from konsensus.entities.data_types import Proposal, Ballot
from tests.base_test_case import BaseTestCase

PROPOSAL1 = Proposal(caller='cli', client_id=123, input='one')
PROPOSAL2 = Proposal(caller='cli', client_id=125, input='two')
PROPOSAL3 = Proposal(caller='cli', client_id=127, input='tre')


class LeaderTestCases(BaseTestCase):
    MockScout = mock.create_autospec(Scout)
    MockCommander = mock.create_autospec(Commander)

    def setUp(self):
        super().setUp()
        self.MockScout.reset_mock()
        self.MockCommander.reset_mock()
        self.leader = Leader(self.node, ['p1', 'p2'], commander=self.MockCommander, scout=self.MockScout)

    def assertScoutStarted(self, ballot_num):
        self.MockScout.assert_called_once_with(self.node, ballot_num, ["p1", 'p2'])
        scout = self.MockScout(self.node, ballot_num, ['p1', 'p2'])
        scout.start.assert_called_once_with()

    def assertNoScout(self):
        self.assertFalse(self.leader.scouting)

    def assertCommanderStarted(self, ballot_num: Ballot, slot: int, proposal: Proposal):
        self.MockCommander.assert_called_once_with(self.node, ballot_num, slot, proposal, ["p1", "p2"])
        commander = self.MockCommander(self.node, ballot_num, slot, proposal, ["p1", "p2"])
        commander.start.assert_called_with()

    def active_leader(self):
        self.leader.active = True

    def fake_proposal(self, slot, proposal):
        self.leader.proposals[slot] = proposal

    def test_propose_inactive(self):
        """A PROPOSE received while inactive spawns a scout"""
        self.node.fake_message(Propose(slot=10, proposal=PROPOSAL1))
        self.assertScoutStarted(Ballot(0, "F999"))

    def test_propose_scouting(self):
        """A PROPOSE received while already scouting is ignored"""
        self.node.fake_message(Propose(slot=10, proposal=PROPOSAL1))
        self.node.fake_message(Propose(slot=10, proposal=PROPOSAL1))
        self.assertScoutStarted(Ballot(0, "F999"))

    def test_propose_active(self):
        """A PROPOSE received while active spawns a commander"""
        self.active_leader()
        self.node.fake_message(Propose(slot=10, proposal=PROPOSAL1))
        self.assertCommanderStarted(Ballot(0, "F999"), 10, PROPOSAL1)

    def test_propose_already(self):
        """A PROPOSE for a slot already in use is ignored"""
        self.active_leader()
        self.fake_proposal(10, PROPOSAL2)
        self.node.fake_message(Propose(slot=10, proposal=PROPOSAL1))
        self.assertEqual(self.MockCommander.mock_calls, [])

    def test_commander_finished_preempted(self):
        """When a commander is preempted, the ballot num is incremented, and the leader is inactive, but no scout is
        spawned
        """
        self.active_leader()
        self.node.fake_message(Propose(slot=10, proposal=PROPOSAL1))
        self.node.fake_message(Preempted(slot=10, preempted_by=Ballot(22, "XXXX")))
        self.assertEqual(self.leader.ballot_num, Ballot(23, "F999"))
        self.assertNoScout()
        self.assertFalse(self.leader.active)

    def test_scout_finished_adopted(self):
        """When a scout finishes and the leader is adopted, accepted proposals are merged and the leader becomes active
        """
        self.leader.spawn_scout()
        self.leader.proposals[9] = PROPOSAL2
        self.node.fake_message(Adopted(ballot_num=Ballot(0, "F999"), accepted_proposals={10: PROPOSAL3}))
        self.assertNoScout()
        self.assertTrue(self.leader.active)
        self.assertEqual(self.leader.proposals, {9: PROPOSAL2, 10: PROPOSAL3})

    def test_scout_finished_preempted(self):
        """When a scout finishes and the leader is preempted, the leader is inactive & its ballot num is updated"""
        self.leader.spawn_scout()
        self.node.fake_message(Preempted(slot=None, preempted_by=Ballot(22, "F999")))
        self.assertNoScout()
        self.assertEqual(self.leader.ballot_num, Ballot(23, "F999"))
        self.assertFalse(self.leader.active)


if __name__ == '__main__':
    unittest.main()
