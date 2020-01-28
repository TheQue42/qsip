from __future__ import annotations
import datetime
import sys
import socket
from qsip.common import *
from qsip.header import *
from qsip.common.utils import *
from qsip.message import *
from threading import Timer
from qsip.stack.transport import *
from qsip.stack.txn import *


class QSipUa(TxnUser):  # We dont really need the interface-concept...DuckTyping.

    def __init__(self,
                 localUdpInfo: IpSrc,
                 localTcpInfo: IpSrc,
                 outgoingProxyUri=None,  # Uri as String
                 auth_info=None):

        """Initialize the SIP service."""
        if auth_info is not None:
            assert isinstance(auth_info, dict), "Authentication info should be supplied in dict{username/password}"
            self._username = auth_info["username"]
            self._password = auth_info["password"]

        if outgoingProxyUri is not None:
            self._outgoingProxyInfo = SipUri.createFromString(outgoingProxyUri)
        # print("IN1", localUdpInfo, type(localTcpInfo))
        # print("IN2", localTcpInfo, type(localTcpInfo))
        assert isinstance(localUdpInfo, IpSrc) and isinstance(localTcpInfo, IpSrc), \
            "Local IP cfg NOT supplied as dict{addr/port}"

        self._udpSource = localUdpInfo
        self._tcpSource = localTcpInfo

        self._messageQueue = []
        self._tpMgr = QSipTransport(self._udpSource, self._tcpSource)
        self.txnList = {}

    def bindToNetwork(self, **kwargs):
        self._tpMgr.bind(self._udpSource, self._tcpSource)

    def addLocalPort(self):
        # We might want to send of lots of ports...need this?
        pass

    def sendRegister(self, dstAddress, dstPort, dstUri):
        """"""
        # TODO: Impl
        pass

    def registerUser(self, username: str, password: str):
        """Send REGISTER to proxy_address"""
        # TODO: Handle 401 Auth.
        # TODO: Check returned ;expires=,
        # Start Timer for Re-Registration with half that value.

        self._username = username
        self._password = password


    # Send Stateless Request.
    def sendRequest(self, *,
                    req_method,
                    request_uri: str,
                    next_hop: NextHop,
                    req_from=None,
                    req_to=None,
                    req_body="",
                    copy_req_uri_to_to=True):


        if req_to is None and copy_req_uri_to_to:
            req_to = dict()
            req_to["uri"] = request_uri
            req_to["display_name"] = "auto-filled"
        else:
            if "display_name" not in req_to.keys():
                req_to["display_name"] = ""

        assert isinstance(req_from, dict), "No valid"
        if "display_name" not in req_from.keys():
            req_from["display_name"] = ""

        msgRequest = Request(method=req_method,
                             from_info=req_from,
                             to_info=req_to,
                             request_uri=request_uri,
                             body=req_body)

        if req_method != "INVITE":
            txn = NonInviteClientTxn(msgRequest, self, timer_t1=0.1)
        else:
            txn = InviteClientTxn(msgRequest, self)

        self.txnList[txn.id()] = txn
        txn.sendRequest(self._udpSource, next_hop)

    def testStuff(self):
        test = SipUri(user="", addr="10.1.1.2", port=5060, tag=genRandomIntString())
        test2 = SipUri(user="pelle", addr="10.1.1.2", port=5060, tag=genRandomIntString())
        # print("Result: ", test2, "host", test.host, "user:", test2.user, "tags:", test.uri_params)
        print(test.uri_params)

    def txnFailed(self, txn: Txn, reason: str = ""):
        print("QSip_UA: Transaction Failed With", reason, "Id:", txn.id())
        self.sendRequest(req_method="MESSAGE",
                         request_uri="taisto@nisse.se", next_hop=NextHop("10.9.24.1", 5060, "UDP"),
                        req_from={"uri": "sip:kenneth@ip-s.se", "display_name": "Kenneth Den Store"},
                        # TODO Cant add custom from-tag.
                        req_to={"uri": "taisto@ip-s.se", "display_name": "TaistoQvist"},
                        req_body="hejsan")
        sys.exit()
    def txnTerminate(self, txn: Txn, reason: str = ""):
        print("Transaction Terminated", txn.Id())