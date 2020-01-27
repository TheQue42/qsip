#!/usr/bin/env python3

#import time

import sys
from qsip.header import IpSrc, NextHop, IpDst

#sys.path.append('D:\\repos\\qsip\\qsip')
sys.path.append('D:\\repos\\qsip') # The logics of import's while developing.
#print("sys.path", sys.path, "name", __name__)
from qsip.ua import QSipUa

from qsip.common import *
#import Thread import Timer
from threading import Timer
import time

def printaHello(aa, bb, *args, **kwargs):
    print("Current time2: ", time.time())
    print(f"Hello: a:[{type(aa)}], and b:[{type(bb)}]",
          "A1:", args, "A2:", kwargs)


if __name__ == "__main__":
    method = "InVite"
    q = QSipUa(IpSrc("", 5060, PROTOCOL.UDP),
               IpSrc("", 0, PROTOCOL.TCP))
    if False:
        q.sendRequest(req_method="MESSAGE",
                  request_uri="taisto@nisse.se", next_hop=NextHop("10.9.24.1", 5060, "UDP"),
                  req_from={"uri": "sip:kenneth@ip-s.se", "display_name": "Kenneth Den Store"},  # Cant add custom from-tag.
                  req_to={"uri": "taisto@ip-s.se", "display_name": "TaistoQvist"},
                  req_body="hejsan")
    #sys.exit()
    p1 = IpSrc("10.1.1.1", 5555)
    p2 = IpDst("10.1.1.1", 5555)
    print(f"P1: {p1}, p2: {p2}, equal: {p1 == p2}")
#m = [mm for mm in  if mm == method]
