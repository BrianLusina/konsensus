from collections import namedtuple


Proposal = namedtuple("Proposal", ["caller", "client_id", "input"])
Ballot = namedtuple("Ballot", ["n", "leader"])
