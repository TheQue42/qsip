class GenericSipError(Exception):
    pass

class NotYetImplemented(GenericSipError):
    pass

class HeaderError(GenericSipError):
    """When trying to add/modify incorrectly"""
    pass

class ParseError(GenericSipError):
    pass

class HeaderOnlyAllowedOnce(HeaderError):
    pass

class MissingMandatoryHeader(HeaderError):
    pass

class UnsupportedHeader(HeaderError):
    pass

class InvalidParameter(HeaderError):
    pass

class ParameterExists(HeaderError):
    pass

class UriParseError(ParseError):
    pass

class ContentLengthMismatch(ParseError):
    pass

class MessageTooBig(ParseError):
    pass

