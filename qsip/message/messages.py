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
                 request_uri=None,
                 body: str,
                 copy_req_uri_to_to=True):
        """

        :type headers: HeaderList
        :type method: str or MethodEnum
        """
        self._method = MethodEnum.get(method)
        self.headers = HeaderList()
        self.request_uri = str()
        if request_uri is not None:
            if not request_uri.find("sip:", 0, 4):
                self.request_uri = "sip:" + request_uri
            else:
                self.request_uri = request_uri
            # TODO: Search for, and escape weird chars...

            if to_info is None and copy_req_uri_to_to :
                self.headers[HeaderEnum.To]["uri"] = request_uri
                self.headers[HeaderEnum.To]["display_name"] = "AutoFilled"

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