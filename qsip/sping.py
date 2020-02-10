#!/usr/bin/env python3

# import time

import sys
# from qsip.header import IpSrc, NextHop, IpDst
import time
from qsip.common import *
from qsip.header import *
sys.path.append('D:\\repos\\qsip')  # The logics of import's while developing.....
from qsip.stack.ua import QSipUa
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s: %(message)s',
    stream=sys.stderr,
)
log = logging.getLogger('main')

def ObjDump(obj, prefix=None, all=False):
    p = prefix if not None else type(obj)
    for o in dir(obj):
        value = str(getattr(obj, o))
        if re.search("method", value) and not all:
            continue
        print(f"obj[{p}].{o} = ", getattr(obj, o))


if __name__ == "__main__":
    method = "InVite"
    q = QSipUa(IpSrc("", 5060, PROTOCOL.UDP))  #, IpSrc("", 6050, "UDP"))  #
    q.bindToNetwork()
    #ch = NameAddress.fromString(HeaderEnum.FROM, '  sip:bob@lab4.net;tag=4b454dbb')
    #print("ch is", ch)
    if 1 == 0:
        q.sendRequest(req_method="INVITE",
                      request_uri="taisto@nisse.se", next_hop=NextHop("10.9.24.1", 5060, "UDP"),
                      req_from={"uri": "sip:kenneth@ip-s.se", "display_name": "Kenneth Den Store"},
                      # Cant add custom from-tag.
                      req_to={"uri": "taisto@ip-s.se", "display_name": "TaistoQvist"},
                      req_body="hejsan")

