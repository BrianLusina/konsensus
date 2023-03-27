import unittest
from unittest.mock import patch, Mock
from konsensus.entities.data_types import Proposal, Ballot
from konsensus.entities.messages_types import Prepare, Promise, Adopted, Preempted
from konsensus.models.roles.scout import Scout
from konsensus.constants import PREPARE_RETRANSMIT
from tests.base_test_case import BaseTestCase

PROPOSAL1 = Proposal(caller='test', client_id=111, input='uno')
PROPOSAL2 = Proposal(caller='test', client_id=222, input='dos')
PROPOSAL3 = Proposal(caller='cli', client_id=127, input='tres')


class ScoutTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.scout = Scout(self.node, Ballot(10, 10), peers=["p1", "p2", "p3"])

    @patch.object(Scout, "send_prepare")
    def test_start(self, send_prepare: Mock):
        """Start() just calls send_prepare"""
        self.scout.start()
        send_prepare.assert_called_once_with()

    def test_send_prepare(self):
        """send_prepare does what it says, repeatedly"""
        self.scout.send_prepare()
        self.assertMessage(["p1", "p2", "p3"], Prepare(ballot_num=Ballot(10, 10)))
        self.assertNoMessages()
        self.network.tick(PREPARE_RETRANSMIT)
        self.assertMessage(["p1", "p2", "p3"], Prepare(ballot_num=Ballot(10, 10)))

    @unittest.skip("IndexError being thrown as sent messages are not available in list, need to investigate")
    def test_promise(self):
        """After a quorum of matching PROMISEs, the scout finishes and sends an ADOPTED containing only the
        highest-numbered accepted proposals"""
        self.scout.send_prepare()
        self.assertMessage(["p1", "p2", "p3"], Prepare(ballot_num=Ballot(10, 10)))
        for acceptor in "p1", "p3":
            accepted_proposals = {
                "p1": {1: (Ballot(5, 5), PROPOSAL1), 2: (Ballot(6, 6), PROPOSAL2)},
                "p3": {1: (Ballot(5, 99), PROPOSAL1), 2: (Ballot(6, 99), PROPOSAL2)}
            }[acceptor]
            self.verifyAcceptedProposals(accepted_proposals)
            self.node.fake_message(
                Promise(ballot_num=Ballot(10, 10), accepted_proposals=accepted_proposals), sender=acceptor)
        self.assertMessage(["F999"],
                           Adopted(ballot_num=Ballot(10, 10), accepted_proposals={1: PROPOSAL1, 2: PROPOSAL2}))
        self.assertUnregistered()

    def test_promise_preempted(self):
        """PROMISEs with different ballot numbers mean preemption"""
        self.scout.send_prepare()
        self.assertMessage(["p1", "p2", "p3"], Prepare(ballot_num=Ballot(10, 10)))
        accepted_proposals = {}
        self.verifyAcceptedProposals(accepted_proposals)
        self.node.fake_message(Promise(ballot_num=Ballot(99, 99), accepted_proposals=accepted_proposals), sender="p2")
        self.assertMessage(["F999"], Preempted(slot=None, preempted_by=Ballot(99, 99)))

    def test_update_accepted_empty(self):
        """update_accepted does nothing with an empty set of accepted proposals"""
        self.scout.update_accepted({})
        self.assertEqual(self.scout.accepted_proposals, {})

    def test_update_accepted_no_overlaps(self):
        """update_accepted, with no slot overlaps, simply creates a new dictionary"""
        self.scout.accepted_proposals[9] = (Ballot(9, 9), PROPOSAL1)
        self.scout.update_accepted({
            10: (Ballot(10, 10), PROPOSAL2),
            11: (Ballot(10, 10), PROPOSAL3),
        })
        self.assertEqual(self.scout.accepted_proposals, {
            9: (Ballot(9, 9), PROPOSAL1),
            10: (Ballot(10, 10), PROPOSAL2),
            11: (Ballot(10, 10), PROPOSAL3),
        })

    def test_update_accepted_highest_ballot_wins(self):
        """Where a value for a slot already exists, update_accepted keeps the proposal with the highest ballot number"""
        self.scout.accepted_proposals[9] = (Ballot(9, 1), PROPOSAL1)
        self.scout.accepted_proposals[10] = (Ballot(10, 99), PROPOSAL1)
        self.scout.update_accepted({
            9: (Ballot(9, 99), PROPOSAL2),
            10: (Ballot(10, 1), PROPOSAL3),
        })
        self.assertEqual(self.scout.accepted_proposals, {
            9: (Ballot(9, 99), PROPOSAL2),
            10: (Ballot(10, 99), PROPOSAL1)
        })


if __name__ == '__main__':
    unittest.main()
