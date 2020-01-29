import socket
import datetime
import sys
from qsip.common import *
from qsip.header import *
from qsip.common.utils import *
from qsip.message import *
import asyncio, logging, threading, warnings


logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-10s) %(message)s',
)

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
        if self._transport is not None:
            old_peer = self._transport.get_extra_info("peername")
            new_peer = transport.get_extra_info("peername")
            warnings.warn(
                "Reinitializing transport connection from %s to %s", old_peer, new_peer
            )

    def datagram_received(self, data, addr):
        print("UdpReader:", addr, data)

    def error_received(self, err):
        print("UdpReader: Error", err)

MAX_UDP_DATA = 4096

class NetReaderThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None, transport_mgr=None, address=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         daemon=daemon)
        self.transport_mgr = transport_mgr
        self.socket = None
        assert isinstance(address, IpSrc)
        self.address = address  # Must contain IP addresses

    async def readData(self, loop):
        data = await loop.sock_recv(self.socket, MAX_UDP_DATA)
        print(data.decode())
        return data

    def socketHandler(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.readData(loop))
        pass

    def useEndpoint(self):
        loop = asyncio.new_event_loop()
        t = loop.create_datagram_endpoint(UdpReader, family=socket.AF_INET,
                                          local_addr=(self.address.addr, self.address.port))
        loop.run_until_complete(t)
        loop.run_forever()
        print("Done:", t)

    def run(self):
        print("THREAD: We've got tp:", self.address, "\n")
        if self.address.proto == PROTOCOL.UDP and False:
            self.useEndpoint()
        elif self.address.proto == PROTOCOL.UDP:
            my_socket = create_socket(self.address.proto, IP_VERSION.V4)
            if bind_socket(my_socket, bindAddress=self.address.addr, bindPort=self.address.port):
                self.socket = my_socket
                #logging.debug("\nSocket Bound in THREAD", my_socket.getsockname())
                self.socketHandler()
        else:
            print("TCP NOT SUPPORTED", self.addresses)
        pass


class QSipTransport(metaclass=Singleton):

    def __init__(self, **kwargs):
        # Since we're binding and connecting the socket towards each specific dstAddr, we need to keep track of which is
        # which. Its currently based ONLY on key="addr", but with TCP support, we're gonna have to change that,
        # to include port+protocol TODO: TCP/UDP
        print("Initializing Singleton Transport Manager")
        self._connectedSockets = dict()
        self._udpThreads = []
        self._tcpThreads = []
        self._connectedSockets[PROTOCOL.UDP] = {}  # Keyed on DstIp
        self._connectedSockets[PROTOCOL.TCP] = {}  # Keyed on DstIp

    def listenOnSocket(self, source: IpSrc = IpSrc("",0, PROTOCOL.TCP) ):
        pass


    def bind(self, *localSources: IpSrc):
        assert len(localSources) > 0, "We need some ports!"
        udpPorts = [p for p in localSources if p.proto == PROTOCOL.UDP and p.port != 0]
        tcpPorts = [p for p in localSources if p.proto == PROTOCOL.TCP and p.port != 0]
        for p in localSources:
            if p.proto == PROTOCOL.UDP:
                thread_udp = NetReaderThread(target=NetReaderThread, transport_mgr=self, address=p)
                self._udpThreads.append(thread_udp)
                thread_udp.start()
            elif p.proto == NetReaderThread.TCP:
                thread_tcp = NetReaderThread(target=NetReaderThread, transport_mgr=self, address=p)
                self._tcpThreads.append(thread_tcp)
                thread_tcp.start()
            else:
                pass
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
