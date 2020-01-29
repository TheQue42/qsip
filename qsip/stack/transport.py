import socket
import datetime
import sys
from qsip.common import *
from qsip.header import *
from qsip.common.utils import *
from qsip.message import *
import asyncio, logging, threading


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        #print("__CALL__", list(cls._instances.keys()), "args", args, "kwargs", kwargs )
        if cls not in cls._instances.keys():
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


class UdpReader(asyncio.DatagramProtocol):
    """"""
    def __init__(self):
        print("Starting UDP Reader")
        self.transport = ""
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print("UdpReader:", addr, data)

    def error_received(self, err):
        print("UdpReader: Error", err)


class ProtocolReader(threading.Thread):

    def __init__(self, group=None, target=None, name=None, protocol : PROTOCOL = PROTOCOL.UDP,
                 transport_mgr= None, addresses=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         daemon=daemon)
        self.transport_mgr = transport_mgr
        assert isinstance(addresses, dict)
        self.addresses = addresses # Must contain IP addresses

    def readUdpSocketData(self):
        buffer = ""
        pass

    def run(self):
        print("THREAD: We've got tp:", self.transport_mgr, "Address", self.addresses)
        #loop = asyncio.get_event_loop()
        #transport = loop.create_datagram_endpoint(UdpReader, local_addr=(local_port.addr, local_port.port))

        pass


class QSipTransport(metaclass=Singleton):

    def __init__(self, **kwargs):
        # Since we're binding and connecting the socket towards each specific dstAddr, we need to keep track of which is
        # which. Its currently based ONLY on key="addr", but with TCP support, we're gonna have to change that,
        # to include port+protocol TODO: TCP/UDP
        print("Initializing Singleton Transport Manager")
        self._connectedSockets = dict()
        self._localBound = dict()
        self._connectedSockets[PROTOCOL.UDP] = {}  # Keyed on DstIp
        self._connectedSockets[PROTOCOL.TCP] = {}  # Keyed on DstIp

    def listenOnSocket(self, source: IpSrc = IpSrc("",0, PROTOCOL.TCP) ):
        pass


    def bind(self, *localSources: IpSrc):
        assert len(localSources) > 0, "We need some ports!"
        for local_port in localSources:
            print("LocalPort: ", local_port)
            # TODO: Don't accept a real IP and also 0.0.0.0? Which to choose?
            if local_port.port == 0:
                print("BAD PORT - We need a port number!", local_port)
                continue
            thread = ProtocolReader(target=ProtocolReader, transport_mgr=self,
                                protocol=local_port.proto, addresses={local_port.addr: local_port.port})
            self._localBound[local_port] = thread
            thread.start()

            #my_socket = create_socket(local_port.proto, IP_VERSION.V4)
            #if bind_socket(my_socket, bindAddress=local_port.addr, bindPort=local_port.port):
                #self._localBound[local_port] = socket

    def getUdpSocket(self, destination: IpDst, source: IpSrc = None) -> socket:
        if destination.addr not in self._connectedSockets[destination.proto].keys():
            mysocket = create_socket(destination.port, IP_VERSION.V4)
            src = IpSrc("", 0, PROTOCOL.UDP) if source is None else source
            if bind_socket(mysocket, bindAddress=src.addr, bindPort=src.port):
                # We need to connect, to get local Ip:port
                local_address, local_port = connect_socket(mysocket, destination.addr, destination.port)
                if local_port > 0:
                    self._connectedSockets[destination.proto][destination.addr] = (mysocket, local_address, local_port)
                    return mysocket, local_address, local_port
                else:
                    # Error connecting socket
                    return None  # TODO: Errorhandling.
            else:
                # Error binding socket
                return None  # TODO: Errorhandling.
            return None, "", 0
        else:
            return self._connectedSockets[destination.proto][destination.addr]
