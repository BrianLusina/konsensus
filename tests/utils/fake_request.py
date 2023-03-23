from typing import Callable


class FakeRequest:
    def __init__(self, node, input_value, callback: Callable):
        self.node = node
        self.input_value = input_value
        self.callback = callback

    def start(self):
        self.callback(('ROTATED', self.node, self.input_value))
