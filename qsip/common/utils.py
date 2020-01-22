import hashlib
from qsip.header import *

"""
Via: SIP/2.0/UDP __VIA_HOST__;rport;branch=z9hG4bK__VIA_BRANCH__\r
Route: __ROUTE_URI__\r
Max-Forwards: 70\r
From: __FROM_HEADER__\r
To: __TO_HEADER__\r
Call-ID: __CALL_ID__\r
CSeq: __CSEQ_NUMBER__ __METHOD__\r
User-Agent: Sping/0.0.0.0.0.1\r
Contact: __CONTACT_URI__\r
Expires: 0\r
Content-Length:  0\r
\r
"""

def populateMostMandatoryHeaders(headers : HeaderList):
    cseq = CseqHeader(MethodEnum.INVITE, 5, cseqParam="Nej")
    subject = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2", subjectParam2=222)
    call-id = SimpleHeader(HeaderEnum.CALL_ID, "", subjectParam2=222)
    via = CustomHeader(hname="Via", value="SIP/2.0/UDP __VIA_HOST__:__VIA_PORT__ ;rport;branch=z9hG4bK" + viaBranch)
    userAgent = CustomHeader(hname="User-Agent", value="Sping/0.0.0.0.0.1")

    pass

def calc_digest_response(self,
                         username: str,
                         realm: str,
                         password: str,
                         method: str,
                         uri: str,
                         nonce: str,
                         nonce_counter: str,
                         client_nonce: str) -> str:
    """
    Digest Authentication
    """
    HA1 = hashlib.md5()
    pre_HA1 = ":".join((username, realm, password))
    HA1.update(pre_HA1.encode())
    pre_HA2 = ":".join((method, uri))
    HA2 = hashlib.md5()
    HA2.update(pre_HA2.encode())
    nc = nonce_counter  ### TODO: Support nonce-reuse?
    list = (HA1.hexdigest(), nonce, nc, client_nonce, "auth", HA2.hexdigest())
    print("List is: ", list)
    preRsp = ":".join(list)
    response = hashlib.md5()
    response.update(preRsp.encode())
    return response.hexdigest()

