import datetime
import sys
import socket
from qsip.common import *
from qsip.header import *
from qsip.common.utils import *
from qsip.message import *
from threading import Timer

class QSipTransport:

    def __init__(self, *localSources, **kwargs):
        # Since we're binding and connecting the socket towards each specific dstAddr, we need to keep track of which is
        # which. Its currently based ONLY on key="addr", but with TCP support, we're gonna have to change that,
        # to include port+protocol TODO: TCP/UDP
        self._socketStorage = dict()
        self._ports = dict()
        self._ports[PROTOCOL.UDP] = []
        self._ports[PROTOCOL.TCP] = []
        for p in localSources:
            self._ports[p.proto].append(p)

        self._socketStorage[PROTOCOL.UDP] = {}
        self._socketStorage[PROTOCOL.TCP] = {}
        self._localUdp = self._ports[PROTOCOL.UDP]
        self._localTcp = self._ports[PROTOCOL.TCP]

    def get_connected_socket(self, dstInfo: IpDst) -> socket:

        src_addr = self._localUdp.addr
        src_port = self._localUdp.port
        print("Param IS:", type(dstInfo), dstInfo, "ISTRUE:", dstInfo.proto == PROTOCOL.UDP)
        if dstInfo.proto == PROTOCOL.UDP:
            if dstInfo.addr not in self._socketStorage[proto].keys():
                mysocket = create_socket(proto, IP_VERSION.V4)

                if bind_socket(mysocket, bindAddress=src_addr, bindPort=src_port):
                    # We need to connect, to get local Ip:port
                    local_address, local_port = connect_socket(mysocket, dstInfo.addr, dstInfo.port)
                    if local_port > 0:
                        self._socketStorage[proto][dst_addr] = (mysocket, local_address, local_port)
                        return mysocket, local_address, local_port
                    else:
                        # Error connecting socket
                        return None  # TODO: Errorhandling.
                else:
                    # Error binding socket
                    return None  # TODO: Errorhandling.
                return None, "", 0
            else:
                return self._socketStorage[proto][dstInfo.addr]
        else:
            return None, "", 0

class QSipUa:

    def __init__(self,
                 localUdpInfo: IpSrc,
                 localTcpInfo: IpSrc,
                 outgoingProxyUri = None,  # Uri as String
                 auth_info=None):

        """Initialize the SIP service."""
        if auth_info is not None:
            assert isinstance(auth_info, dict), "Authentication info should be supplied in dict{username/password}"
            self._username = auth_info["username"]
            self._password = auth_info["password"]

        # TODO: PreCreate Route-header.
        if outgoingProxyUri is not None:
            self._outgoingProxyInfo = SipUri.createFromString(outgoingProxyUri)
        print("IN1", localUdpInfo, type(localTcpInfo))
        print("IN2", localTcpInfo, type(localTcpInfo))
        assert isinstance(localUdpInfo, IpSrc) and isinstance(localTcpInfo, IpSrc),\
            "Local IP cfg NOT supplied as dict{addr/port}"
        ## TODO  Validate Dict entry.
        self._udpSource = localUdpInfo
        self._tcpSource = localTcpInfo
        #print("LocalIPInfo set to: ", localUdpInfo, localTcpInfo)
        assert localTcpInfo.port == 0, "TCP Currently NOT supported"
        self._messageQueue = []
        self._tpMgr = QSipTransport(self._udpSource, self._tcpSource)

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

    def sendOnTimer(self, msg, sock, next_hop):
        print("======== Sending ============", datetime.datetime.now())
        print(str(msg))
        print("======== Sending ============")
        bytesToSend = str(msg).encode()
        # TODO: Check socket is valid? getpeername, getsockname?


        result = sock.sendto(bytesToSend, (next_hop["addr"], next_hop["port"]))

        if result != len(bytesToSend):
            sock.close()
            print("Failed Sending Entire messages")
            # TODO: Remove from socket storage

    # Send Stateless Request.
    def sendRequest(self, *,
                    req_method,
                    request_uri: str,
                    next_hop: NextHop,
                    req_from=None,
                    req_to=None,
                    req_body="",
                    copy_req_uri_to_to=True) -> (int, Msg):

        # TODO: We shouldnt fetch a socket until we pop it from the queue.
        current_socket, local_addr, local_port = self._tpMgr.get_connected_socket(next_hop)

        if local_port == 0 or current_socket is None:
            print("Failed binding/connecting")
            return 0

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

        msgRequest.informSocketSrcInfo(local_addr, local_port)  # TODO: Send along in constructor, or callback later?

        queueEntry = dict()
        queueEntry["msg"] = msgRequest
        queueEntry["next_hop"] = next_hop
        queueEntry["socket"] = current_socket

        self._messageQueue.append(queueEntry)
        t = Timer(1.0, self.sendOnTimer, [msgRequest, current_socket, next_hop])
        t.start()
        return 0, msgRequest

    def checkAndPrint(self, a, b):
        print(f"A: {a}, B:{b}")
        return a == b

    def testStuff(self):
        test = SipUri(user="", addr="10.1.1.2", port=5060, tag=genRandomIntString())
        test2 = SipUri(user="pelle", addr="10.1.1.2", port=5060, tag=genRandomIntString())
        # print("Result: ", test2, "host", test.host, "user:", test2.user, "tags:", test.uri_params)
        print(test.uri_params)


if __name__ == "__main__":
    method = "InVite"

    # m = [mm for mm in  if mm == method]
    print(method)
