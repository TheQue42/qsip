class GenericSipError(Exception):
    pass


class InvalidHeader(GenericSipError):
    pass

class HeaderOnlyAllowedOnce(GenericSipError):
    pass

class ParameterExists(GenericSipError):
    pass


class InvalidParameter(GenericSipError):
    pass
