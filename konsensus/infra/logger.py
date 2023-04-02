"""
SimTimeLogger is an implementation of the LoggerAdapter
"""
import logging


class SimTimeLogger(logging.LoggerAdapter):
    """
    SimTimeLogger is a LoggerAdapter
    """

    # pylint: disable-next=missing-function-docstring
    def process(self, msg, kwargs):
        return f"T={self.extra['network'].now} {msg}", kwargs

    # pylint: disable-next=invalid-name
    def getChild(self, name):
        """
        Get Child logger
        """
        return self.__class__(
            self.logger.getChild(name), {"network": self.extra["network"]}
        )
