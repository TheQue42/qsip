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

    def sendRequest(self, method: str, request_uri: str, body: str, headers=None) -> bool:
        """
        """
        if not isinstance(headers, dict):
            return False;
        if not validateDefaultHeaders(headers):
            return False

        populateMandatoryHeaders(headers)


    def sendMessage(self, dst_addr: str, dst_port: int, request_uri: str, body: str) -> int:
        ### TODO: We'll most definitely need ;rport. ==> Currently hardcoded into via-header.

        current_socket, local_addr, local_port = self.get_socket(dst_addr, dst_port)

        if local_port == 0 or current_socket is None:
            print("Failed binding/connecting")
            return 0
        print(f"Source is: {local_addr}, Port: {local_port}, with socket: {current_socket.fileno()}")

        msg = str(requestTemplate)
        msg = msg.replace(templateMap["method"], "OPTIONS")
        msg = msg.replace(templateMap["requri"], request_uri)
        msg = msg.replace(templateMap["from"], "sip:taisto@trippelsteg.se")
        msg = msg.replace(templateMap["to"], request_uri)
        msg = msg.replace(templateMap["route"], "sip:proxy@10.9.24.1:5060")
        viaHost = local_addr + ":" + str(local_port)
        msg = msg.replace(templateMap["viahost"], viaHost)
        #msg = msg.replace(templateMap["viabranch"], generateViaBranch())
        msg = msg.replace(templateMap["contact"], "sip:taisto@10.9.24.44:5060")
        msg = msg.replace(templateMap["callid"], "dsadasdasda")
        msg = msg.replace(templateMap["cseqnr"], "5")
        msg = msg.replace("__CONTENT_LENGTH__", str(len(body)) )
        msg = msg + "\r"
        msg = msg + body
        result = current_socket.sendto(msg.encode(), (dst_addr, dst_port))

        if result != len(msg.encode()):
            current_socket.close()
            print("Failed Sending Entire messages")
            # TODO: Remove from socket storage
        return result

    def checkAndPrint(self, a, b):
        print(f"A: {a}, B:{b}")
        return a == b

    def testStuff(self):
        digestResponse = calc_digest_response("bob","bee.net", "bob", "REGISTER", "sip:bee.net",
                                               "49e4ab81fb07c2228367573b093ba96efd292066",
                                               "00000001", "8d82cf2d1e7ff78b28570c311d2e99bd", "HejsanSvejsan")
        print("Challenge Response: ", digestResponse)

        #    result = sipSender.sendMessage("10.9.24.132", 5060, "sip:taisto@trippelsteg.se", "HejsanSvejsan1")

        method1 = "InVite"
        method2 = MethodEnum.INVITE
        #print("Vals: ", list(MethodEnum))
        m = getMethod("InvITE")
        M2 = MethodEnum.get("CaNCeL")
        print("Found M:", m, "aND", M2)
        sys.exit()
        h = HeaderList()
        na1 = NameAddress(HeaderEnum.FROM, uri="taisto@kenneth.qvist", display_name="Taisto k. Qvist", param1="p1", param2="p2")
        Cseq = CseqHeader(MethodEnum.INVITE, 5, cseqParam="Nej")
        subject2 = SimpleHeader(HeaderEnum.SUBJECT, "Subject-2", subjectParam2=222)
        custom1 = CustomHeader(hname="MyCustomHeader", value="MyCustomValue", customParam1="FortyTwo", X=0.1)
        vvv = dict()
        vvv["One"] = "realm=trippelsteg.se"
        vvv["Two"] = "digest"
        vvv["Three"] = "cnonce=9823139082013982"
        print("Types:", type(vvv), type(vvv.keys()))

        custom2 = CustomHeader(hname="Authorization", value=vvv, customParam2="FortyThree", X=0.2)

        hlist = HeaderList()
        hlist.add(na1)
        hlist.add(Cseq)
        hlist.add(subject1)
        hlist.add(custom1)

        #print("vars:", vars(hlist))
        print("------------------")
        test = str(hlist)
        print(test)
        print("HasHeader1", hlist.hasHeader(HeaderEnum.CALL_ID))
        print("HasHeader2", hlist.hasHeader(HeaderEnum.SUBJECT))
        print("IsEqual:", HeaderEnum.SUBJECT == "SubJect")


if __name__ == "__main__":
    method = "InVite"
      
    #m = [mm for mm in  if mm == method]
    print(method)
