import logging


class SimTimeLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return "T=%.3f %s" % (self.extra['network'].now, msg), kwargs

    def getChild(self, name):
        return self.__class__(self.logger.getChild(name), {'network': self.extra['network']})
