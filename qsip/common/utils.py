import hashlib
from qsip.header import *


def createRandomString(size=31):
    return str(random.randint(0, 2 ** size - 1))

def populateMostMandatoryHeaders(headers : HeaderList):

    cseq = CseqHeader(MethodEnum.INVITE, 5)
    subject = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2")
    call_id = SimpleHeader(HeaderEnum.CALL_ID, createRandomString() + "@IP_Domain")
    maxForwards = SimpleHeader(HeaderEnum.MAX_FWD, "70")
    viaH = ViaHeader(PROTOCOL.UDP) # TODO: ;branch as parameter
    userAgent = CustomHeader(hname="User-Agent", value="Sping/0.0.0.0.0.1")

    headers.add(cseq)
    headers.add(subject)
    headers.add(call_id)
    headers.add(viaH)
    headers.add(userAgent)
    headers.add(maxForwards)
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

