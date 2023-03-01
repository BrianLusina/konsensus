from . import Role
from ..node import Node
from ...constants import NULL_BALLOT
from konsensus.entities.messages_types import Accepting, Promise, Accepted


class Acceptor(Role):
    """
    This implements the Acceptor Role in the protocol. Therefore, it must store the ballot number representing
    its most recent promise, along with the set of accepted proposal for each slot. It then responds to Prepare
    and Accept messages according to the protocol

    This looks like a Simple Paxos with the addition of slot numbers to the messages
    """

    def __init__(self, node: Node):
        super().__init__(node)
        self.ballot_num = NULL_BALLOT
        # {slot: (ballot_num, proposal)}
        self.accepted_proposals = {}
    
    def do_prepare(self, sender, ballot_num: NULL_BALLOT):
        if ballot_num > self.ballot_num:
            self.ballot_num = ballot_num
            # We have heard from a scout, so it might be the next leader
            self.node.send([self.node.address], Accepting(leader=sender))
        
        self.node.send([sender], Promise(ballot_num=self.ballot_num, accepted_proposals=self.accepted_proposals))
    
    def do_accept(self, sender, ballot_num, slot, proposal):
        if ballot_num >= self.ballot_num:
            self.ballot_num = ballot_num
            acc = self.accepted_proposals
            if slot not in acc or acc[slot][0] < ballot_num:
                acc[slot] = (ballot_num, proposal)
            
        self.node.send([sender], Accepted(slot=slot, ballot_num=self.ballot_num))
