from enum import Enum

from qsip.common import *
from qsip.header import *
from qsip.common.enums import *

class Msg:
    """Base class for SIP Request and Response"""
    # TODO: Make it impossible to instansiate base Msg class?

    def __init__(self, *, method: str, body="", header_list: HeaderList):
        """" Base class for SIP Messages """
        self._method = method
        self.body = body[:]  # TODO: Needed?
        self._headers = header_list
        # TODO: Add content-type and Content-Length

    def setFrom(self, *, uri: str, display_name: str) -> None:
        f_header = NameAddress(HeaderEnum.FROM, uri=uri)
        self._headers._headerList[HeaderEnum.FROM] = f_header

    def setTo(self, *, uri: str, display_name: str) -> None:
        t_header = NameAddress(HeaderEnum.TO, uri=uri)
        self._headers._headerList[HeaderEnum.FROM] = t_header

    def setToTag(self, generate=True):
        pass

    def setFromTag(self, generate=True):
        pass

    def addHeader(self, header: Header) -> None:
        self._headers.add(header)

    def getTopHeader(self, htype: HeaderEnum) -> Header:
        return self.getHeaders(htype)[0]

    def getHeaders(self, htype=None) -> HeaderList:
        """Return a new list with only the headers specified"""

        if htype is not None:
            assert isinstance(htype, HeaderEnum), "Must be HeaderEnum"
            hlist = [hh for hh in self._headers if hh.htype == htype]
            return hlist
        else:
            return self._headers


    def setSocketInfo(self, address: str, port: int, proto = PROTOCOL.UDP):
        self.srcIp = address
        self.srcPort = port
        self.protocol = proto
        viaList = self._headers._headerList[HeaderEnum.VIA]
        if isinstance(viaList, list):
            viaList[0].setSentBy(address, port)
        else:
            viaList.setSentBy(address, port)

    @staticmethod
    def isRequest(data: str) -> bool:
        line1, rest = data.split(sep="\n", maxsplit=1)
        mg = re.search("^(\w*)\s+sip:(.*)\s+SIP/2.0", line1)
        return mg

    @staticmethod
    def isResponse(data: str) -> bool:
        if re.match("SIP/2.0", data):
            return True
        else:
            return False

    def __str__(self):
        #print("Running __str__ in:; ", __class__, "headers:", self.headers)
        all_string = ""
        if isinstance(self, Request):
            all_string = self._method.value + " " + self._request_uri + " SIP/2.0"
        if isinstance(self, Response):
            all_string = "SIP/2.0 " + self._response_code + self._response_text
        all_string = all_string + "\r\n"
        #print(f"StartingLine: {all_string}")
        all_string = all_string + str(self._headers)
        if len(self.body) > 0:
            # TODO: Add Content-Type and Content-Length(If TCP)
            all_string = all_string + "\r\n"
            all_string = all_string + self.body
        return all_string


class Request(Msg):
    """Base class for SIP_Requests

    Main tasks (eventually):
    - Validate requirements for various kinds of requests such as:
      - Contact in INVITE and SUBSCRIBE requests (NOTIFY after rfc6665)
    - 2.5 million other things.

    """
    @classmethod
    def create(cls, *,
               method,
               from_info=None,
               to_info=None,
               request_uri: str,
               body: str):

        method = MethodEnum.fromStr(method)

        toH = NameAddress(HeaderEnum.TO, uri=to_info["uri"], display_name=to_info["display_name"])
        fromH = NameAddress(HeaderEnum.FROM, uri=from_info["uri"], display_name=from_info["display_name"])
        header_list = HeaderList()
        header_list.add(fromH)
        header_list.add(toH)
        populateMostMandatoryHeaders(header_list, method)
        Request(method=method,
                from_info=fromH,
                to_info=toH,
                request_uri=SipUri.createFromString(request_uri),
                header_list=header_list,
                body=body)


    def __init__(self,
                 method: MethodEnum,
                 from_info: NameAddress,
                 to_info: NameAddress,
                 request_uri: SipUri,
                 header_list: HeaderList,
                 body: str):
        self._request_uri = request_uri
        super().__init__(method=method, body=body, header_list=header_list)


    @classmethod
    def fromString(cls, data):
        lines = data.splitlines()
        mg = re.search("^(\w*)\s+sip:(.*)\s+SIP/2.0", lines[0])
        if mg:
            method = MethodEnum.fromStr(mg.group(1))
            request_uri = SipUri.createFromString(mg.group(2))
        else:
            assert False, "Bad Initial Request Parse" #THROW...
        headerList = HeaderList()
        print(f"FullString \n{lines}")
        for count, h in enumerate(lines[1:], 2):
            print(f"Parsing recv: {h}")
            if h != "":
                found = False
                for htype in list(HeaderEnum):
                    header_name, header_value = h.split(":", maxsplit=1)
                    if header_name.lower() == htype.value.lower():
                        #print(f"Matched {header_name} against {htype.value} with value: [{header_value}]")
                        found = True
                        break
                if found:
                    headerFound = Header.fromString(htype, header_value) # TODO: Exception handling
                    if headerFound is not None:
                        headerList.add(headerFound)
                    else:
                        print(f"\n\nFAILED CREATING HEADER {htype}")
                else:
                    print(f"Misidentified: {h}")
            else:
                onlyBodyLeft = True
                body = lines[count]
                break
        print(f"Body is: {body}")
        return Request(method=method, from_info="", to_info="", request_uri=request_uri, header_list=headerList, body=body)

class Response:

    def __init__(self, response_code: int, response_text: str, headers: HeaderList, body=""):
        self._response_code = response_code
        self._response_text = response_text
        self.headers = headers

    @classmethod
    def fromString(cls, data):
        return cls

def createReponse(self, request: Request, response_code: int, response_text: str) -> Response:
    return Response(response_code, response_text, request.getHeaders())


if __name__ == "__main__":
    print("__file__", __file__, "name: ", __name__, ", vars: ", vars())