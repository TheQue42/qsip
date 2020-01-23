from enum import Enum

from qsip.common import *
from qsip.header import *
from qsip.common.enums import *

class Msg:
    """Base class for SIP Request and Response"""
    # TODO: Make it impossible to instansiate base Msg class?

    def __init__(self, *, body="", headers: HeaderList):
        """" Base class for SIP Messages """
        self.body = body[:]
        self.headers = headers
        populateMostMandatoryHeaders(self.headers)
        #print(vars(self.headers))
        # TODO: Add content-type and Content-Length

    def setFrom(self, *, uri: str, display_name: str) -> None:
        f_header = NameAddress(HeaderEnum.FROM, uri=uri)
        self.headers.headerList[HeaderEnum.FROM] = f_header

    def setTo(self, *, uri: str, display_name: str) -> None:
        t_header = NameAddress(HeaderEnum.TO, uri=uri)
        self.headers.headerList[HeaderEnum.FROM] = t_header

    def setToTag(self, generate=True):
        pass

    def setFromTag(self, generate=True):
        pass

    def addHeader(self, header: Header) -> None:
        self.headers.add(header)

    def getHeaders(self, htype=None) -> HeaderList:
        """Return a new list with only the headers specified"""

        if htype is not None:
            assert isinstance(htype, HeaderEnum), "Must be HeaderEnum"
            hlist = HeaderList()
            [[hlist.add(hh)] for hh in self.headers if hh.htype == htype]
            #print("hlist:", hlist )
            return hlist
        else:
            return self.headers


    def informSocketSrcInfo(self, address: str, port: int, proto = PROTOCOL.UDP):
        self.srcIp = address
        self.srcPort = port
        self.protocol = proto
        viaList = self.headers.headerList[HeaderEnum.VIA]
        if isinstance(viaList, list):
            viaList[0].setSentBy(address, port)
        else:
            viaList.setSentBy(address, port)

    def __str__(self):
        #print("Running __str__ in:; ", __class__, "headers:", self.headers)
        all_string = ""
        if isinstance(self, Request):
            all_string = self._method.value + " " + self.request_uri + " SIP/2.0"
        if isinstance(self, Response):
            all_string = "SIP/2.0 " + self._response_code + self._response_text
        all_string = all_string + "\r\n"
        #print(f"StartingLine: {all_string}")
        all_string = all_string + str(self.headers)
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
    - Whatever else I can think of...

    """

    def __init__(self, *,
                 method,
                 from_info=None,
                 to_info=None,
                 request_uri=str,
                 body: str):
        """

        :type headers: HeaderList
        :type method: str or MethodEnum
        """
        self._method = MethodEnum.get(method)
        self.request_uri = addSipToUri(request_uri)
        self.headers = HeaderList()

        # TODO: Search for, and escape weird chars...

        toH = NameAddress(HeaderEnum.TO, uri=to_info["uri"], display_name=to_info["display_name"])
        fromH = NameAddress(HeaderEnum.FROM, uri=from_info["uri"], display_name=from_info["display_name"])
        self.headers.add(fromH)
        self.headers.add(toH)
        # Constructor fills in most mandatory headers.
        super().__init__(body=body, headers=self.headers)

class Response:

    def __init__(self, response_code: int, response_text: str, headers: HeaderList, body=""):
        self._response_code = response_code
        self._response_text = response_text
        self.headers = headers

    def create(self, request : Request, response_code: int, response_text: str):
        return Response(response_code, response_text, request.headers)

if __name__ == "__main__":
    print("__file__", __file__, "name: ", __name__, ", vars: ", vars())