"""
Timer represents timer callbacks in the system
"""
from typing import Union, Callable


class Timer:
    """
    Timer class handle timer callbacks
    """

    def __init__(
            self, expires: Union[int, float], address: str, callback: Callable
    ) -> None:
        self.expires = expires
        self.address = address
        self.callback = callback
        self.cancelled = False

    def __eq__(self, other: "Timer") -> bool:
        return self.expires == other.expires

    def __lt__(self, other: "Timer"):
        return self.expires < other.expires

    def __gt__(self, other: "Timer"):
        return self.expires > other.expires

    # pylint: disable-next=inconsistent-return-statements
    def __cmp__(self, other: "Timer"):
        if self.expires < other.expires:
            return -1
        if (self.expires == other.expires) or (self.expires > other.expires):
            return +1

    # pylint: disable-next=missing-function-docstring
    def cancel(self):
        self.cancelled = True
