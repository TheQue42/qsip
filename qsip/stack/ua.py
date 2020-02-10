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

def routeRequest(sip_request: Request):
    """Request Router. We check
        Route-Uri or request-Uri:
        ;transport-parameter.
        TODO: FQDN-loopkup?
    """
    next_ip = ""
    next_port = 0
    topRoute = None
    try:
        topRoute = sip_request.getTopHeader(HeaderEnum.ROUTE)
        next_hop_uri = topRoute.getUri();
        host = next_hop_uri.host_port
    except HeaderNotFound as err:
        next_hop_uri = sip_request._request_uri
        host = next_hop_uri.host_port
    print(f"Next_Hop_Uri: {next_hop_uri}, hp:{host} X:", type(host))
    return (host.addr, host.port, PROTOCOL.UDP)


class QSipUa(TxnUser):  # We dont really need the interface-concept...DuckTyping.

    def __init__(self, *localPorts,
                 outgoingProxyUri: str = None,  # Uri as String
                 auth_info: dict = None):

        """Initialize the SIP service."""
        if auth_info is not None:
            assert isinstance(auth_info, dict), "Authentication info should be supplied in dict{username/password}"
            self._username = auth_info["username"]
            self._password = auth_info["password"]

        if outgoingProxyUri is not None:
            self._outgoingProxyInfo = SipUri.createFromString(outgoingProxyUri)
        # print("IN1", localUdpInfo, type(localTcpInfo))
        # print("IN2", localTcpInfo, type(localTcpInfo))
#        assert isinstance(localUdpInfo, IpSrc) and isinstance(localTcpInfo, IpSrc), \
 #           "Local IP cfg NOT supplied as dict{addr/port}"

        self._udpSource = [p for p in localPorts if p.proto == PROTOCOL.UDP and p.port != 0]
        self._tcpSource = [p for p in localPorts if p.proto == PROTOCOL.TCP and p.port != 0]
        #print(f"udp, {type(self._udpSource)}, type2 {type(self._tcpSource)}", self._udpSource, self._tcpSource)
        assert len(self._udpSource) + len(self._tcpSource) > 0, "We need at LEAST one port please!"
        self._messageQueue = []
        self._tpMgr = QSipTransport()
        self._txnMgr = QTxnMgr()
        self.txnList = {}

    def bindToNetwork(self, **kwargs):
        self._tpMgr.bind(self._udpSource + self._tcpSource)

    def addLocalPort(self):
        # We might want to send FROM a lots of ports...need this?
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


    def sendRequest(self, *,
                    req_method,
                    request_uri: str,
                    next_hop: IpDst = None,
                    req_from=None,
                    req_to=None,
                    req_body="",
                    copy_req_uri_to_to=True, **kwargs):


        if req_to is None and copy_req_uri_to_to:
            req_to = dict()
            req_to["uri"] = request_uri
            req_to["display_name"] = "auto-filled"
        else:
            if "display_name" not in req_to.keys():
                req_to["display_name"] = ""

        assert isinstance(req_from, dict), "No valid From header"
        if "display_name" not in req_from.keys():
            req_from["display_name"] = ""

        msgRequest = Request.create(method=req_method,
                                    from_info=req_from, to_info=req_to,
                                    request_uri=request_uri,
                                    body=req_body,
                                    **kwargs)  # Additional Headers
        #msgRequest.setTopViaBranch("kdjsaklkjlwkje23")
        next_hop = routeRequest(msgRequest)
        print(f"nexthop: {next_hop}", str(msgRequest.getHeaders(HeaderEnum.ROUTE)))
        if next_hop.isResolved():
            self._txnMgr.sendRequest(self, msgRequest, self._udpSource[0], next_hop=next_hop)
        else:
            print(msgRequest.getHeaders(HeaderEnum.CUSTOM))

    def txnFailed(self, txn: Txn, reason: str = ""):
        print(f"QSipUA: Transaction({txn.id()}) Failed With: {reason}")

    def testStuff(self):
        test = SipUri(user="", addr="10.1.1.2", port=5060, tag=genRandomIntString())
        test2 = SipUri(user="pelle", addr="10.1.1.2", port=5060, tag=genRandomIntString())
        print(test.uri_params)

    def txnTerminate(self, txn: Txn, reason: str = ""):
        print("Transaction Terminated", txn.Id())