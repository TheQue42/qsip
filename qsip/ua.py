#import time

import socket
    
class QSipUa:

    def __init__(self,
                 localIpInfo=None,
                 outgoingProxyInfo=None,
                 protocol = "UDP"):

        """Initialize the SIP service."""
        self._username = ""
        self._password = ""

        if  outgoingProxyInfo is None:
            self._outgoingProxyInfo = dict(addr="", port=0)
        else:
            # TODO  Validate Dict entry.
            # outgoingProxyInfo{"addr"} = IPv4/Host/IPv6 (eventually)
            # outgoingProxyInfo{"port"} = DNS NAPTR instead? 0 TODO: Should mean NAPTR?
            # TODO: PreCreate Route-header.
            self._outgoingProxyInfo = outgoingProxyInfo

        if localIpInfo is None:
            # TODO  Validate Dict entry.
            self._localIpInfo = dict(addr="", port=0)
        else:
            self._localIpInfo = localIpInfo
            print("LocalIPInfo set to: ", localIpInfo)

        self._protocol = PROTOCOL.UDP #For now.

        # Since we're binding and connecting the socket towards each specific dstAddr, we need to keep track of which is
        # which. Its currently based on key="addr", but with TCP support, we're gonna have to change that. TODO: TCP/UDP
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
        Send any SIP Request
        :param method:
        :param request_uri:
        :param body:
        :param headers:
        :return:
        """
        if not isinstance(headers, dict):
            return False;
        if not validateDefaultHeaders(headers):
            return False

        populateMandatoryHeaders(headers)



    def sendMessage(self, dst_addr: str, dst_port: int, request_uri: str, body: str) -> int:
        """Send a SIP messages to a specific IP-destination, with a specific dst-uri?"""
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


if __name__ == "__main__":
    method = "InVite"
      
    #m = [mm for mm in  if mm == method]
    print(method)
