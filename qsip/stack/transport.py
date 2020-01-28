import socket
import datetime
import sys
from qsip.common import *
from qsip.header import *
from qsip.common.utils import *
from qsip.message import *

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
            # Dont accept a real IP and 0.0.0.0
            self._ports[p.proto].append(p)

        self._socketStorage[PROTOCOL.UDP] = {}  # Keyed on DstIp
        self._socketStorage[PROTOCOL.TCP] = {}  # Keyed on DstIp

    def getUdpSocket(self, destination: IpDst, source: IpSrc = None) -> socket:

        if destination.addr not in self._socketStorage[destination.proto].keys():
            mysocket = create_socket(destination.proto, IP_VERSION.V4)
            src = IpSrc("", 0, PROTOCOL.UDP) if source is None else source
            if bind_socket(mysocket, bindAddress=src.addr, bindPort=src.port):
                # We need to connect, to get local Ip:port
                local_address, local_port = connect_socket(mysocket, destination.addr, destination.port)
                if local_port > 0:
                    self._socketStorage[destination.proto][destination.addr] = (mysocket, local_address, local_port)
                    return mysocket, local_address, local_port
                else:
                    # Error connecting socket
                    return None  # TODO: Errorhandling.
            else:
                # Error binding socket
                return None  # TODO: Errorhandling.
            return None, "", 0
        else:
            return self._socketStorage[destination.proto][destination.addr]
