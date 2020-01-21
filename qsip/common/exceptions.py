class GenericSipError(Exception):
    pass


class InvalidHeader(GenericSipError):
    pass


class ParameterExists(GenericSipError):
    pass
