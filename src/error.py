
class ValidationError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)

    def __repr__(self):
        return self.msg
