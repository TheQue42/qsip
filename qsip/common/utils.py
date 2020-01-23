import hashlib
import random
#from qsip.header import *


def genRandomIntString(size=31) ->  str:
    return str(random.randint(0, 2 ** size - 1))

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
    mlist = (HA1.hexdigest(), nonce, nc, client_nonce, "auth", HA2.hexdigest())
    print("List is: ", mlist)
    preRsp = ":".join(mlist)
    response = hashlib.md5()
    response.update(preRsp.encode())
    return response.hexdigest()


def addSipToUri(uri: str) -> str:
    nuri = "sip:" + uri if uri.find("sip:", 0, 4) < 0 else uri
    return nuri

    if uri.find("sip:", 0, 4) < 0:
        return "sip:" + uri
    else:
        return uri
