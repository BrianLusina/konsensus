class Timer(object):
    def __init__(self, expires, address, callback) -> None:
        self.expires = expires
        self.address = address
        self.callback = callback
        self.cancelled = False

    def __eq__(self, other: object) -> bool:
        return self.expires == other.expires
    
    def cancel(self):
        self.cancelled = True
