"""
While it's not included in this implementation, the component model allows us to swap in a real-world network implementation, 
communicating between actual servers on a real network, with no changes to the other components. 
Testing and debugging can take place using the simulated network, with production use of the library operating over real network hardware.
"""

from typing import Dict, Optional, List, Callable
import random
import heapq
from functools import partial
from copy import deepcopy
from .models.node import Node
from .models.timer import Timer


class Network:
    """
    The Network class provides a simple simulated network with these capabilities and also simulates packet loss and message propagation delays.
    
    Timers are handled using Python's heapq module, allowing efficient selection of the next event. Setting a timer involves pushing a Timer object onto the heap. 
    Since removing items from a heap is inefficient, cancelled timers are left in place but marked as cancelled.
    
    Message transmission uses the timer functionality to schedule a later delivery of the message at each node, using a random simulated delay. 
    We again use functools.partial to set up a future call to the destination node's receive method with appropriate arguments.
    
    Running the simulation just involves popping timers from the heap and executing them if they have not been cancelled and if the destination node is still active.    
    """
    PROP_DELAY = 0.03
    PROP_JITTER = 0.02
    DROP_PROB = 0.05

    def __init__(self, seed) -> None:
        self.nodes: Dict[str, Node] = {}
        self.rnd = random.Random(seed)
        self.timers: List[Timer] = []
        self.now = 1000.0

    def new_node(self, address: Optional[str] = None) -> Node:
        node = Node(self, address=address)
        self.nodes[node.address] = node
        return node

    def run(self):
        while self.timers:
            next_timer = self.timers[0]
            if next_timer.expires > self.now:
                self.now = next_timer.expires
            heapq.heappop(self.timers)
            if next_timer.cancelled:
                continue
            if not next_timer.address or next_timer.address in self.nodes:
                next_timer.callback()

    def stop(self):
        self.timers = []

    def set_timer(self, address, seconds: int, callback: Callable) -> Timer:
        timer = Timer(self.now + seconds, address, callback)
        heapq.heappush(self.timers, timer)
        return timer

    def send(self, sender, destinations, message):
        sender.logger.debug(f"sending {message} to {destinations}")

        # avoid aliasing by making a closure containing distinct deep copy of message for each destination
        def sendto(dest, message):
            if dest == sender.address:
                # reliably deliver local messages with no delay
                self.set_timer(sender.address, 0, lambda: sender.receive(sender.address, message))
            elif self.rnd.uniform(0, 1.0) > self.DROP_PROB:
                delay = self.PROP_DELAY + self.rnd.uniform(-self.PROP_JITTER, self.PROP_JITTER)
                self.set_timer(dest, delay, partial(self.nodes[dest].receive, sender.address, message))

        for dest in (d for d in destinations if d in self.nodes):
            sendto(dest, deepcopy(message))
