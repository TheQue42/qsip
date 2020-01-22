from enum import Enum

class PROTOCOL(Enum):
    TCP = 0  # SO_STREAM??
    UDP = 1
    SCTP = 2


class IP_VERSION(Enum):
    V6 = 0  #AF_INET6?
    V4 = 1  #AF_INET?

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
            #print("Comparing:", self.value, "With:", other, self.name.lower() == other.lower())
            if isinstance(other, str):
                return self.name.lower() == other.lower()
            else:
                assert False, "Can only compare with str(ings) or correct-type ENUMs"

    # We need to be hashable, and defining __eq__() undefines the default __hash__
    # It should(?) be safe to reuse the Object-class version, since we're not storing anything else
    # in this class
    def __hash__(self) -> int:
        return super().__hash__()

    # ::is? ::convert? ::fromStr?
    def get(name: str):
        #print("Will search for", name)
        m = [meth for meth in list(MethodEnum) if meth == name]
        return m[0]

def getMethod(name: str):
    m = [mm for mm in list(MethodEnum) if mm == name]
    return m[0]
