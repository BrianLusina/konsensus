import unittest
from konsensus.models.roles.acceptor import Acceptor
from konsensus.entities.data_types import Ballot, Proposal
from konsensus.entities.messages_types import Prepare, Promise, Accepting
from tests.base_test_case import BaseTestCase


class AcceptorTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.acceptor = Acceptor(self.node)
    
    def assertState(self, ballot_num, accepted_proposals):
        self.assertEqual(self.acceptor.ballot_num, ballot_num)
        self.assertEqual(self.acceptor.accepted_proposals, accepted_proposals)
    
    def test_prepare_new_ballot(self):
        """On PREPARE with a new ballot, Acceptor returns a PROMISE with the new ballot
        and send an ACCEPTING message"""
        proposal = Proposal('cli', 123, 'INC')
        self.acceptor.accepted_proposals = {33: (Ballot(19, 19), proposal)}
        self.acceptor.ballot_num = Ballot(10, 10)
        self.node.fake_message(Prepare(
                               # newer than the acceptor's ballot_num
                               ballot_num=Ballot(19, 19)), sender='SC')
        self.assertMessage(['F999'], Accepting(leader='SC'))
        accepted_proposals = {33: (Ballot(19, 19), proposal)}
        self.verifyAcceptedProposals(accepted_proposals)
        self.assertMessage(['SC'], Promise(
                           # replies with updated ballot_num
                           ballot_num=Ballot(19, 19),
                           # including accepted_proposals ballots
                           accepted_proposals=accepted_proposals))
        self.assertState(Ballot(19, 19), {33: (Ballot(19, 19), proposal)})


if __name__ == '__main__':
    unittest.main()
