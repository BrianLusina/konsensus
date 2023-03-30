"""
Constants
"""
from .entities.data_types import Ballot, Proposal


JOIN_RETRANSMIT = 0.7
CATCHUP_INTERVAL = 0.6
ACCEPT_RETRANSMIT = 1.0
PREPARE_RETRANSMIT = 1.0
INVOKE_RETRANSMIT = 0.5
LEADER_TIMEOUT = 1.0
NULL_BALLOT = Ballot(-1, -1)  # sorts before real ballots
NOOP_PROPOSAL = Proposal(None, None, None)  # No-op to fill empty slots
