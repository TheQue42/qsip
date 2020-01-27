#!/usr/bin/env python3

#import time

from qsip.ua import QSipUa
from qsip.common import *
from qsip.header import createUriFromString
#import Thread import Timer
from threading import Timer
import time

def printaHello(aa, bb, *args, **kwargs):
    print("Current time2: ", time.time())
    print(f"Hello: a:[{type(aa)}], and b:[{type(bb)}]",
          "A1:", args, "A2:", kwargs)


if __name__ == "__main__":
    method = "InVite"
    q = QSipUa()    # TODO: Param: StateLess || TransactionStateful ?
    # q.sendMessageRequest(request_uri="taisto@nisse.se", next_hop={"addr": "10.9.24.1", "port":5060},
    #                      msg_from={"uri": "sip:kenneth@ip-s.se", "display_name": "Kenneth Den Store"},  # Cant add custom from-tag.
    #                      msg_to={"uri": "taisto@ip-s.se", "display_name": "TaistoQvist"},
    #                      msg_body="hejsan")
    #q.testStuff()
    uri = createUriFromString("sip:taisto@ip-s.se:5006")
    print(f"Uri-parsed: {uri}")

#m = [mm for mm in  if mm == method]
