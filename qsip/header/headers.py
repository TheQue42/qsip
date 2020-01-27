import random
from enum import Enum
from qsip.common.enums import *
from qsip.common.exceptions import *
from qsip.common.utils import *
import re

from collections import namedtuple
from typing import NamedTuple, Union


class NextHop(NamedTuple):
    addr: str
    port: int
    proto: PROTOCOL = PROTOCOL.UDP


_IpSrc = NamedTuple("IpSrc", [("addr", str),
                              ("port", int),
                              ("proto", PROTOCOL)])


class IpInfo(_IpSrc):
    def __new__(cls, addr, port, proto=PROTOCOL.UDP):
        #        print("Addr:", addr, "port:", port, "proto: ", proto)
        if isinstance(proto, str):
            p = PROTOCOL.UDP  # TODO: Match
        else:
            p = proto
        return super(IpInfo, cls).__new__(cls, addr, port, p)

    def __init(self, addr, port, proto):
        
# TODO: Use alias
class IpSrc(IpInfo):
    pass

class IpDst(IpInfo):
    pass


class SipHost:

    def isFqdn(self, addr: str):
        return False

    def __init__(self, addr: str, port=0):
        assert len(addr) > 0, "Zero length address/host"
        if self.isFqdn(addr):  # TODO FqDN logic NOT defined
            self._fqdn = addr
            self.addr = None
            self._resolved = False
        else:
            self.addr = addr
            self.port = port
            if addr.find(":") < 0:
                self.ipVersion = IP_VERSION.V4
            else:
                self.ipVersion = IP_VERSION.V6
            self._resolved = True

    def isResolved(self):
        return self._resolved

    def resolve(self, naptr=False) -> list:
        # Set value in self.addr?
        return []
        # Do lots of RFC3263 Magic

    def __str__(self):
        if self.port is None or self.port == 0:
            return self.addr
        else:
            return self.addr + ":" + str(self.port)


class UriParams:
    def __init__(self, **kwargs):
        self.parameters = kwargs

    def __str__(self):
        params = str()
        for paramKey in self.parameters.keys():
            params = params + ";" + paramKey + "=" + str(self.parameters[paramKey])
        return params


class SipUri:

    def __init__(self, *, user: str, addr: str, port=0, **kwargs):
        self.user = user
        self.host = SipHost(addr, port)
        self.uri_params = UriParams(**kwargs)

    def __str__(self):
        if self.user is None or len(self.user) == 0:
            return "sip:" + str(self.host) + str(self.uri_params)
        else:
            return "sip:" + self.user + "@" + str(self.host) + str(self.uri_params)

    def __radd__(self, other):
        if isinstance(other, str):
            return other + str(self)
        else:
            raise TypeError

    def __add__(self, other):
        if isinstance(other, str):
            return str(self) + other
        else:
            raise TypeError

    @classmethod
    def createUriFromHost(cls, host: SipHost):
        return cls(user="", addr=host.addr, port=host.port)

    @classmethod
    def createFromString(cls, uri_string: str):
        # TODO: Lots of clever parsing
        # Strip whitespace?? TODO: strip <>
        # uri_string = "sip:taisto@ip-s.se:4444 ; ; param1=JoahssånX; param2=23131 kalle"
        uri = ""
        # print(f"Incoming:[{uri_string}]")
        if uri_string.find("sip", 0, 4) == 0:
            uri = uri_string[4:]
        else:
            uri = uri_string
        hasAtSign = uri.find("@")
        if hasAtSign >= 0:
            assert hasAtSign > 0, "Invalid URI without <<User>>@ in front of @"
            user = uri[0:hasAtSign]
            uri = uri[hasAtSign + 1:]
        else:
            user = ""
        hasColon = uri.find(":")
        if hasColon >= 0:
            assert hasColon > 0, "Invalid URI hostname!"
            host = uri[0:hasColon]
            port = uri[hasColon + 1:]
            pmatch = re.match("(\d+)\s*(.*)", port)
            assert pmatch.group(1) and int(pmatch.group(1)) > 0, "Invalid URI with ':' but no or invalid port number"
            port = pmatch.group(1)
            uri = pmatch.group(2)
        else:
            pmatch = re.search("(^[a-zA-Z0-9.-]+)(.*)", uri)  # Strip whitespace
            host = pmatch.group(1)
            uri = pmatch.group(2)
            port = 0
        uri = re.sub(" +;", ";", uri)  # Strip whitespace
        uri = re.sub("; +", ";", uri)  # Strip whitespace
        # uri = re.sub(";+", ";", uri)  # Strip whitespace

        # Lets extract any parameters
        params = dict()
        # print(f"Param search starting with: [{uri}]")
        while len(uri) > 0:
            # TODO: Update Regexp to match TOKEN-def. This wont handle ;p="kalle petter"
            #       and CERTAINLY doesnt support the ims-bug with multiple identical charging-params,
            #       and the \w allows åäö in param-name+value which is doubtful.
            # TODO: MUST be updated to support "q=1.0"...
            pmatch = re.search("(;[\w=]+)(.*)", uri)
            if not pmatch:
                break
            else:
                p = pmatch.group(1)
                key, value = p[1:].split("=", )
                if key in params.keys():
                    print("Warning: identical parameters in header!")  # TODO: Use proper LOGGING/WARNING call.
                params[key] = value
                uri = pmatch.group(2)

        # print(f"Lefturi:[{uri}]", "host:", host, "user:", user, "port", port, params) # TODO Log.Log
        return SipUri(user=user, addr=host, port=port)


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
    CUSTOM = ""

    def __eq__(self, other):
        if isinstance(other, HeaderEnum):
            return self.value == other.value
        else:
            if isinstance(other, str):
                return self.name.lower() == other.lower()
            else:
                assert False, "Can only compare with str(ings) or correct-type ENUMs:"

    # We need to be hashable, and defining __eq__() undefines the default __hash__
    # It should(?) be safe to reuse the Object-class version, since we're not storing anything else
    # in this class
    def __hash__(self) -> int:
        return super().__hash__()


_SINGLE_USE_HEADERS = [HeaderEnum.FROM, HeaderEnum.TO, HeaderEnum.CALL_ID, HeaderEnum.CSEQ, HeaderEnum.CONTENT_TYPE]

_VIA_MAGIC_COOKE: str = "z9hG4Bk"


### TODO: Define multiHeader, or SingleHeader to indicate maxNrOfCount.

class Header:
    __MAX_LEN__ = 1024

    # TODO: It would be simpler to indicate what we DO support but:
    # - line-folded headers
    # - escaping rules mania

    # GenericHeader: Value ;param1=Abc ;param2=xyz
    def __init__(self, *, htype: HeaderEnum, hvalues: dict(), **kwargs):
        self.htype = htype
        self.values = hvalues  # copy.deep?
        self.parameters = kwargs  # Param Names in .keys()

    def addParam(self, name: str, value: str, allow_update=False):
        # TODO Append multiple parameters, allowAppend=False
        if str in self.parameters.keys() or allow_update:
            raise InvalidParameter
        self.parameters[name] = value

    def stringifyParameters(self) -> str:
        params = str()
        for paramKey in self.parameters.keys():
            params = params + " ;" + paramKey + "=" + str(self.parameters[paramKey])
        return params

    def __str__(self) -> str:
        # print("Using base-class __str__ for:", self.htype.value)
        hName = self.htype.value
        assert len(self.values.keys()) == 1, "Base-class only handles single value-headers"
        keys = [key for key in self.values.keys()]
        value = self.values[keys[0]]
        return hName + ": " + str(value) + self.stringifyParameters()


class SimpleHeader(Header):

    def __init__(self, htype: HeaderEnum, hvalue: str, **kwargs):
        values = dict()
        values["0"] = hvalue
        super().__init__(htype=htype, hvalues=values, **kwargs)

    # NO overriding of __str__ here. Use base-class


class CseqHeader(Header):

    def __init__(self, method: MethodEnum, number=-1, **kwargs):
        if number < 0:
            number = str(random.randint(0, 2 ** 31 - 1))
        values = {}
        values["method"] = method
        values["number"] = number
        super().__init__(htype=HeaderEnum.CSEQ, hvalues=values, **kwargs)  ### NOTE: We're sending the object..

    def __str__(self) -> str:
        hName = self.htype.value
        return hName + ": " + self.values["method"].value.upper() + " " \
               + str(self.values["number"])  # + self.stringifyParameters() CSeq not allowed to have params...


class ViaHeader(Header):

    def __init__(self, proto: PROTOCOL, host=None, port=0, **kwargs):  # TODO: Via;branch is parameter!
        self.protocol = proto
        assert self.protocol == PROTOCOL.UDP, "Only UDP supported"
        values = {}
        values["sent_by"] = {}
        values["sent_by"]["host"] = host
        values["sent_by"]["port"] = port
        values["prefix"] = "SIP/2.0/" + self.protocol.name
        if "branch" not in kwargs.keys():
            self.branch = _VIA_MAGIC_COOKE + "_" + genRandomIntString(64)
        else:
            assert isinstance(kwargs["branch"], str), ";branch param not supplied as string"
            self.branch = kwargs["branch"]
            kwargs.pop("branch", None)
        super().__init__(htype=HeaderEnum.VIA, hvalues=values, **kwargs)

    def getBranch(self) -> str:
        return self.branch

    def setSentBy(self, host: str, port: int):
        self.values["sent_by"]["host"] = host
        self.values["sent_by"]["port"] = port

    def randomizeBranch(self, incremental: False, addMagicCookie=True):
        if not incremental:
            if addMagicCookie:
                self.branch = _VIA_MAGIC_COOKE
            self.branch = str(random.randint(0, 2 ** 60 - 1))  # TODO: ==>Hex
        else:
            # Here, we'll try increment the (maybe) number after ;branch = z9hG4Bk_<NUMBER>
            try:
                new_branch = self.branch
                if new_branch.find(_VIA_MAGIC_COOKE, 0, len(_VIA_MAGIC_COOKE)) != -1:
                    new_branch = new_branch[len(_VIA_MAGIC_COOKE) + 1:]
                else:
                    pass
                    # Not a magic-Cooke, just a number?
                new_branch = int(new_branch)
                new_branch = new_branch + 1
                if addMagicCookie:
                    self.branch = _VIA_MAGIC_COOKE
                    self.branch = self.branch + "_" + str(new_branch)
                else:
                    self.branch = str(new_branch)
            except:
                # We could of course have used isinstance(self.branch, int) but...
                self.branch = self.branch + "1"

    def __str__(self):
        hName = self.htype.value

        assert self.values["sent_by"]["host"] is not None \
               and self.values["sent_by"]["port"] is not None, "You need to set IP Info"

        host = self.values["sent_by"]["host"]
        port = self.values["sent_by"]["port"]

        if port is None or port <= 0:
            port = 5060

        # TODO: if self.sent_by["host"] == IPv6 ==> [ipv6 reference]
        return hName + ": " + "SIP/2.0/" + self.protocol.name + " " + host + ":" \
               + str(port) + ";branch=" + self.branch + self.stringifyParameters()

        # TODO: Via;branch is parameter!


# Proxy-Authorization: Digest username="goran",realm="ip-solutions.se",
# nonce="Ub8wuFG/L4xKkTQ5UwWt8/vkeVEuPWip",uri="sip:gabriel@ip-solutions.se",
# response="76ab7f721cfca9220ba071c038f83774",algorithm=MD5
class CustomHeader(Header):
    """"
    A Custom header can have one or more values. (But no editing currently)
    TODO: We need to decide if the keys of hvalues["cnonse"] = "skdjakjdk" should be used for anything
          or if we just ignore them as Accept: text/plain, text/html
    """

    def __init__(self, *, hname: str, value, **kwargs):  # NOTE, value may be dict or string.
        self.hname = hname  # Only custom header has to keep track of Header name as string.
        if isinstance(value, dict):
            super().__init__(htype=HeaderEnum.CUSTOM, hvalues=value, **kwargs)
        if isinstance(value, str):
            values = dict()
            values["0"] = value
            super().__init__(htype=HeaderEnum.CUSTOM, hvalues=values, **kwargs)

    def __str__(self):
        hName = self.hname
        hValue = str()
        keyCount = len(self.values.keys())
        for i, val in enumerate(self.values.keys(), 1):
            hValue = hValue + self.values[val]
            if i < keyCount:
                hValue = hValue + ", "
        return hName + ": " + hValue + self.stringifyParameters()


class NameAddress(Header):
    """Any header that contains a URI, with an optional display name, such as  From, To, Contact, Rec/Route:"""
    valid_list = (HeaderEnum.FROM,
                  HeaderEnum.TO,
                  HeaderEnum.ROUTE, HeaderEnum.RECROUTE,
                  HeaderEnum.CONTACT,
                  HeaderEnum.REFER_TO,
                  HeaderEnum.CUSTOM)  # TODO: Not used for validation yet

    def __init__(self, htype: HeaderEnum, uri: str, display_name=None, **kwargs):

        if htype not in NameAddress.valid_list:
            raise GenericSipError

        # We're assuming that "incoming" uri does NOT contain "<>"
        # TODO: Search for, and escape weird chars...
        values = {}
        values["uri"] = addSipToUri(uri)  # Add sip: if needed
        values["display_name"] = display_name
        super().__init__(htype=htype, hvalues=values, **kwargs)

    def __str__(self) -> str:
        hName = self.htype.value
        hValue = ""
        if self.values["display_name"] is not None:
            # TODO: ONLY If display_name contains SPACE or "," add ""
            if self.values["display_name"].find(" ") > 0:
                hValue = '"' + self.values["display_name"] + '"' + " "
            else:
                hValue = self.values["display_name"] + " "

        if len(self.parameters.keys()) > 0:
            return hName + ": " + hValue + "<" + self.values["uri"] + ">" + self.stringifyParameters()
        else:
            return hName + ": " + hValue + self.values["uri"] + self.stringifyParameters()

    def setUri(self, uri: str):
        self.values["uri"] = addSipToUri(uri)


class HeaderList:  # Not really a >> [list()] <<

    def __init__(self):
        self._headerList = dict()

    def add(self, header: Header, addToTop=True) -> bool:
        # TODO: Storing headers in dict/hash is maybe not so good, since it will change the order relative to how
        #       they were added. It wont change inter-(same)-header order, so it wont FAIL, but it might feel weird?
        htype = header.htype
        # print("Adding key: ", htype.name)
        if htype not in self._headerList.keys():
            # print("Adding: ", str(header))
            self._headerList[htype] = [header]
        else:
            if header.htype in _SINGLE_USE_HEADERS:
                # raise HeaderOnlyAllowedOnce
                return False
            if addToTop:
                # TODO Use the end as TOP of message, and then .reverse() during stringification?
                #      Since .insert is quite costly...
                self._headerList[htype].insert(0, header)
            else:
                self._headerList[htype].append(header)
        return True

    def __str__(self) -> str:
        mHeaders = ""
        for hType in self._headerList.keys():
            for hInstance in self._headerList[hType]:
                mHeaders = mHeaders + str(hInstance)
                mHeaders = mHeaders + "\r\n"
        return mHeaders

    def __iter__(self):
        return HeaderIterator(self)

    def hasHeader(self, hType: HeaderEnum) -> int:
        if hType in self._headerList.keys():
            return len(self._headerList[hType])
        else:
            return 0

    def __setitem__(self, key, value):
        if key not in list(HeaderEnum):
            raise InvalidHeader
        self._headerList[key] = value

    def __getitem__(self, key):
        if key not in list(HeaderEnum):
            raise InvalidHeader
        return self._headerList[key]

    def __delitem__(self, key):
        pass

    def __len__(self):
        pass

    def __keytransform__(self, key):
        pass


class HeaderIterator:  # TODO: Filter for iterator?

    def __init__(self, hlist: HeaderList):
        self._headers = hlist
        self._index = 0
        self.all_headers = []
        self.maxCount = 0
        for key in self._headers._headerList.keys():
            # Actual headers are stored in a list as the headerList["type"] = [top, ..., bottom]
            for h in self._headers._headerList[key]:
                self.all_headers.append(h)
                self.maxCount += 1

    def getHeaderCount(self) -> int:
        count = 0
        for key in self._headers._headerList.keys():
            # Actual headers are stored in a list as the headerList["type"] = [top, ..., bottom]
            for h in self._headers._headerList[key]:
                count += 1
        return count
        # hlist = [[hh] for hh in self.headers if hh == htype or True]

    def __next__(self):
        if self._index >= self.maxCount:
            raise StopIteration
        else:
            self._index += 1
            return self.all_headers[self._index - 1]


def populateMostMandatoryHeaders(headers: HeaderList):
    cseq = CseqHeader(MethodEnum.INVITE, 5, order="1")
    subject = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2", order="2")
    call_id = SimpleHeader(HeaderEnum.CALL_ID, genRandomIntString() + "@IP_Domain")
    viaTop = ViaHeader(PROTOCOL.UDP, branch="1231243123", order="4")
    userAgent = CustomHeader(hname="User-Agent", value="Sping/0.0.0.0.0.1", order="5")
    maxForwards = SimpleHeader(HeaderEnum.MAX_FWD, "70", order="6")
    viaBottom = ViaHeader(PROTOCOL.UDP, order="7")
    viaBottom.setSentBy("1.1.1.1", 6050)

    headers.add(cseq)
    headers.add(subject)
    headers.add(call_id)
    headers.add(viaTop)
    headers.add(userAgent)
    headers.add(maxForwards)
    headers.add(viaBottom, False)


if __name__ == "__main__":
    print("__file__", __file__, "name: ", __name__, ", vars: ", vars())
