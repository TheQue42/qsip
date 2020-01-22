import time
import sys
import socket
from qsip.common import *
from qsip.header import *
from qsip.message import *

class QSipUa:

    def __init__(self,
                 localIpInfo=None,
                 outgoingProxyInfo=None,
                 auth_info = None,
                 protocol = "UDP"):

        """Initialize the SIP service."""
        if auth_info is not None:
            assert isinstance(auth_info, dict), "Authentication info should be supplied in dict{username/password}"
            self._username = auth_info["username"]
            self._password = auth_info["password"]

        if  outgoingProxyInfo is None:
            self._outgoingProxyInfo = dict(addr="", port=0)
        else:
            assert isinstance(outgoingProxyInfo, dict), "Not supplied as dict{addr/port}"
            # TODO  Validate Dict entry.
            # outgoingProxyInfo{"addr"} = IPv4/Host/IPv6 (eventually)
            # outgoingProxyInfo{"port"} = DNS NAPTR instead? 0 TODO: Should mean NAPTR?
            # TODO: PreCreate Route-header.
            self._outgoingProxyInfo = outgoingProxyInfo

        if localIpInfo is None:
            self._localIpInfo = dict(addr="", port=0)
        else:
            assert isinstance(localIpInfo, dict), "Not supplied as dict{addr/port}"
            # TODO  Validate Dict entry.
            self._localIpInfo = localIpInfo
            print("LocalIPInfo set to: ", localIpInfo)

        self._protocol = PROTOCOL.UDP #For now.

        # Since we're binding and connecting the socket towards each specific dstAddr, we need to keep track of which is
        # which. Its currently based ONLY on key="addr", but with TCP support, we're gonna have to change that,
        # to include port+protocol TODO: TCP/UDP
        self._socketStorage = {}
        self._messageQueue = []


    def get_socket(self, dst_addr: str, dst_port : int) -> socket:
        if dst_addr not in self._socketStorage.keys():
            mysocket = create_socket(PROTOCOL.UDP, IP_VERSION.V4) ### TQ-TODO: Hardcoded

            if bind_socket(mysocket, bindAddress=self._localIpInfo["addr"], bindPort=self._localIpInfo["port"]):
                # We need to connect, to get local Ip:port
                local_address, local_port = connect_socket(mysocket, dst_addr, dst_port)
                if local_port > 0:
                    self._socketStorage[dst_addr] = (mysocket, local_address, local_port)
                    return mysocket, local_address, local_port
                else:
                    # Error connecting socket
                    bool #TODO: Errorhandling.
            else:
                # Error binding socket
                bool #TODO: Errorhandling.
            return None, "", 0
        else:
            return self._socketStorage[dst_addr]

    def sendRegister(self, dstAddress, dstPort, dstUri):
        """"""
        # TODO: Impl
        bool

    def registerUser(self, username: str, password: str):
        """Send REGISTER to proxy_address"""
        # TODO: Handle 401 Auth.
        # TODO: Check returned ;expires=,
        # Start Timer for Re-Registration with half that value.

        self._username = username
        self._password = password

        #qsip.sendRegister(self._username, self._password)

    def sendRequest(self, *,
                    req_method,
                    request_uri: str,
                    next_hop,
                    req_from=None,
                    req_to=None,
                    req_body="") -> bool:
        """
        :type next_hop: dict
        """
        current_socket, local_addr, local_port = self.get_socket(next_hop["addr"], next_hop["port"])

        msgRequest = Request(method=req_method,
                             from_info=req_from,
                             to_info=req_to,
                             request_uri=request_uri,
                             body=req_body)

        if local_port == 0 or current_socket is None:
            print("Failed binding/connecting")
            return 0

        print(f"Source is: {local_addr}, Port: {local_port}, with socket: {current_socket.fileno()}")
        msgRequest.informSocketSrcInfo(local_addr, local_port)
        print("======== Sending ============")
        print(str(msgRequest))
        print("======== Sending ============")
        bytesToSend = str(msgRequest).encode()
        result = current_socket.sendto(bytesToSend, (next_hop["addr"], next_hop["port"]))

        if result != len(bytesToSend):
            current_socket.close()
            print("Failed Sending Entire messages")
            # TODO: Remove from socket storage
        return result

    def sendMessage(self, *,
                    request_uri: str,
                    next_hop,
                    msg_from=None,
                    msg_to=None,
                    msg_body="") -> int:

        ### TODO: We'll most definitely need ;rport. ==> Currently hardcoded into via-header.
        self.sendRequest(req_method=MethodEnum.MESSAGE,
                         request_uri=request_uri,
                         next_hop=next_hop,
                         req_from=msg_from, req_to=msg_to,
                         req_body=msg_body)

    def checkAndPrint(self, a, b):
        print(f"A: {a}, B:{b}")
        return a == b

    def testStuff(self):
        digestResponse = calc_digest_response("bob","bee.net", "bob", "REGISTER", "sip:bee.net",
                                               "49e4ab81fb07c2228367573b093ba96efd292066",
                                               "00000001", "8d82cf2d1e7ff78b28570c311d2e99bd", "HejsanSvejsan")
        print("Challenge Response: ", digestResponse)
        viaH = ViaHeader(PROTOCOL.UDP)  # TODO: ;branch as parameter
        print("ViaHeader", viaH)

if __name__ == "__main__":
    method = "InVite"
      
    #m = [mm for mm in  if mm == method]
    print(method)
