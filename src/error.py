
class ValidationError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)

    def __repr__(self):
        return self.msg

    @staticmethod
    def field_error(field_name, value):
        return ValidationError("Właściwość " + field_name + " ma niepoprawną wartość [" + str(value) + "]")
