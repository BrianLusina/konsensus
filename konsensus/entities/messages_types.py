from collections import namedtuple


Accepted = namedtuple("Accepted", ["slot", "ballot_num"])
Accept = namedtuple("Accept", ["slot", "ballot_num", "proposal"])
Decision = namedtuple("Decision", ["slot", "proposal"])
Invoked = namedtuple("Invoked", ["client_id", "output"])
Invoke = namedtuple("Invoke", ["caller", "client_id", "input_value"])
Join = namedtuple("Join", [])
Active = namedtuple("Active", [])
Prepare = namedtuple("Prepare", ["ballot_num"])
Promise = namedtuple("Promise", ["ballot_num", "accepted_proposals"])
Propose = namedtuple("Propose", ["slot", "proposal"])
Welcome = namedtuple("Welcome", ["state", "slot", "decisions"])
Decided = namedtuple("Decided", ["slot"])
Preempted = namedtuple("Preempted", ["slot", "preempted_by"])
Adopted = namedtuple("Adopted", ["ballot_num", "accepted_proposals"])
Accepting = namedtuple("Accepting", ["leader"])
