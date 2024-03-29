from __future__ import annotations
from typing import Optional
from konsensus.network import Network
import logging
from konsensus.models.node import Node


class FakeNetwork(Network):
    def __init__(self, seed=1234) -> None:
        super().__init__(seed)
        self.now = 0.0
        self.node = None
        self.ran = False

    def new_node(self, address=None):
        assert not self.node, "FakeNetwork only runs one node"
        self.node = FakeNode(self)
        return self.node

    def run(self):
        self.ran = True

    def tick(self, seconds):
        until = self.now + seconds
        self.timers.sort()
        while self.timers and self.timers[0].expires <= until:
            timer = self.timers.pop(0)
            self.now = timer.expires
            if not timer.cancelled:
                timer.callback()
        self.now = until

    def send(self, sender, destinations, message):
        sender.sent.append((destinations, message))

    def get_times(self):
        return sorted([t.expires - self.now for t in self.timers if not t.cancelled and t.address in self.nodes])


class FakeNode(Node):

    def __init__(self, network: Optional[FakeNetwork] = FakeNetwork()):
        network = network or FakeNetwork()
        super(FakeNode, self).__init__(network, "F999")
        self.unique_id = 999
        self.sent = []
        self.logger = logging.getLogger('node.%s' % (self.address,))

    def register(self, role):
        assert role not in self.roles
        super(FakeNode, self).register(role)

    def unregister(self, role):
        assert role in self.roles
        super(FakeNode, self).unregister(role)

    def fake_message(self, message, sender='F999'):
        for role in self.roles:
            fn = getattr(role, f'do_{type(message).__name__}'.lower())
            fn(sender=sender, **message._asdict())
