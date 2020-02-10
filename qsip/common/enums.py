from __future__ import annotations
from enum import Enum
from qsip.common.exceptions import *

class PROTOCOL(Enum):
    TCP = 0  # SO_STREAM??
    UDP = 1
    SCTP = 2

    def __eq__(self, other):
        if isinstance(other, PROTOCOL):
            return self.value == other.value
        else:
            if isinstance(other, str):
                return self.name.lower() == other.lower()
            else:
                # print("Type is, ", type(other), "is:", other)
                # assert False, "Can only compare with str(ings) or correct-type ENUMs"
                return False

    def __hash__(self) -> int:
        return super().__hash__()

    @classmethod
    def fromStr(cls, proto: str):
        if proto.upper() == "UDP":
            return PROTOCOL.UDP
        else:
            return PROTOCOL.TCP


class IP_VERSION(Enum):
    V6 = 6  # AF_INET6?
    V4 = 4  # AF_INET?


class HeaderEnum(Enum):
    CALL_ID = "Call-ID"
    TO = "To"
    FROM = "From"
    VIA = "Via"
    CSEQ = "CSeq"
    CONTACT = "Contact"
    ROUTE = "Route"
    RECROUTE = "Record-Route"
    REFER_TO = "Refer-To"
    EXPIRES = "Expires"
    SUPPORTED = "Supported"
    WARNING = "Warning"
    ACCEPT = "Accept"
    SERVER = "Server"
    SUBJECT = "Subject"
    USER_AGENT = "User-Agent"
    MAX_FWD = "Max-Forwards"
    CONTENT_TYPE = "Content-Type"
    CONTENT_LENGTH = "Content-Length"
    CUSTOM = ""

    @staticmethod
    def isNameAddress(hType: HeaderEnum):
        return hType in [HeaderEnum.TO, HeaderEnum.FROM, HeaderEnum.ROUTE, HeaderEnum.RECROUTE,
                         HeaderEnum.CONTACT, HeaderEnum.REFER_TO]

    @staticmethod
    def isSimpleHeader(hType: HeaderEnum):
        return hType in [HeaderEnum.MAX_FWD, HeaderEnum.SUBJECT, HeaderEnum.CONTENT_TYPE, HeaderEnum.CONTENT_LENGTH,
                         HeaderEnum.USER_AGENT, HeaderEnum.SERVER, HeaderEnum.CALL_ID, HeaderEnum.EXPIRES]

    def __eq__(self, other):
        if isinstance(other, HeaderEnum):
            return self.value == other.value
        else:
            if isinstance(other, str):
                return self.name.lower() == other.lower()
            else:
                assert False, "Can only compare with str(ings) or correct-type ENUMs:"

    @classmethod
    def fromStr(cls, name: str):
        hmatch = [h for h in list(HeaderEnum) if h.value.upper() == name.upper()]
        if len(hmatch) == 0:
            raise HeaderUnsupported
        return hmatch[0]  # Are we really returning an ENUM CLASS here?

    @staticmethod
    def isSupportedHeader(name:str):
        try:
            h = HeaderEnum.fromStr(name)
            return h
        except HeaderUnsupported:
            return None

    # We need to be hashable, and defining __eq__() undefines the default __hash__
    # It should(?) be safe to reuse the Object-class version, since we're not storing anything else
    # in this class
    def __hash__(self) -> int:
        return super().__hash__()


class MethodEnum(Enum):
    INVITE = "INVITE"
    CANCEL = "CANCEL"
    ACK = "ACK"
    BYE = "BYE"
    OPTIONS = "OPTIONS"
    REGISTER = "REGISTER"
    SUBSCRIBE = "SUBSCRIBE"
    PUBLISH = "PUBLISH"
    NOTIFY = "NOTIFY"
    REFER = "REFER"
    MESSAGE = "MESSAGE"

    def __eq__(self, other):
        if isinstance(other, MethodEnum):
            return self.value == other.value
        else:
            # print("Comparing:", self.value, "With:", other, self.name.lower() == other.lower())
            if isinstance(other, str):
                return self.name.lower() == other.lower()
            else:
                assert False, "Can only compare with str(ings) or correct-type ENUMs"

    # We need to be hashable, and defining __eq__() undefines the default __hash__
    # It should(?) be safe to reuse the Object-class version, since we're not storing anything else
    # in this class
    def __hash__(self) -> int:
        return super().__hash__()

    @classmethod
    def fromStr(cls, name: str):
        #print("Will search for", name.upper())
        m = [meth for meth in list(MethodEnum) if meth.value.upper() == name.upper()]
        assert len(m) > 0, "Bad method spec"
        return m[0]  # Are we really returning an ENUM CLASS here?
