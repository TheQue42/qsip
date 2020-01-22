from enum import Enum

from qsip.common import *
from qsip.header import *
from qsip.common.enums import *

class Msg:
    """Base class for SIP Request and Response"""
    # TODO: Make it impossible to instansiate base Msg class?

    def __init__(self, *, body=""):
        """" Base class for SIP Messages """
        self.body = body[:]
        self.headers = populateMostMandatoryHeaders()

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

    def informSocketSrcInfo(self, address: str, port: int, proto: PROTOCOL):
        self.srcIp = address
        self.srcPort = port
        self.protocol = proto


    def __str__(self):
        if isinstance(self, Request):
            all_string = self._method.value + " " + self._request_uri + " SIP/2.0"
        if isinstance(self, Response):
            all_string = "SIP/2.0 " + self._response_code + self._response_text
        all_string = all_string + "\r\n"
        all_string = str(self.headers)
        if len(self.body) > 0:
            all_string = all_string + "\r\n"
            all_string = all_string + self.body



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

        if request_uri is not None:
            self._request_uri = request_uri
            if copy_req_uri_to_to :
                self.headers[HeaderEnum.To]["uri"] = request_uri
                self.headers[HeaderEnum.To]["display_name"] = "AutoFilled"

        # Constructor fills in most mandatory headers.
        super().__init__(body=body)

class Response:

    def __init__(self, response_code: int, response_text: str, headers: HeaderList, body=""):
        self._response_code = response_code
        self._response_text = response_text
        self.headers = headers

    def create(self, request : Request, response_code: int, response_text: str):
        return Response(response_code, response_text, request.headers)

if __name__ == "__main__":
    print("__file__", __file__, "name: ", __name__, ", vars: ", vars())