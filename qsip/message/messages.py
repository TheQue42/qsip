from enum import Enum

from qsip.common import *
from qsip.header import *

class Msg:
    """Base class for SIP Request and Response"""

    def __init__(self, *, method: MethodEnum, from_info=None, to_info=None, body=""):
        self.body = body[:]
        self.headers = HeaderList()
        self._method = method
        # populateMandatoryHeaders(self.headers)

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


"""
    Cseq = CseqHeader(MethodEnum.INVITE, 5, cseqParam="Nej")
    subject2 = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2", subjectParam2=222)
    custom1 = CustomHeader(hname="MyCustomHeader", value="MyCustomValue", customParam1="FortyTwo", X=0.1)
"""


class Request(Msg):

    def __init__(self, *, method, headers: HeaderList, body: str, request_uri: str):
        method = MethodEnum
        if isinstance(method, str):
            method = MethodEnum.INVITE
            m = [mm for mm in MethodEnum if mm == method]
            print("M", m)
        else:
            assert isinstance(method, Enum)

        if request_uri is None:
            self._request_uri = request_uri
        else:
            self._request_uri = headers.headerList[HeaderEnum.TO]


class Response:

    def __init__(self, response_code: int, response_text: str, headers: HeaderList, body=""):
        self._response_code = response_code
        self._response_text = response_text


if __name__ == "__main__":
    print("__file__", __file__, "name: ", __name__, ", vars: ", vars())