import socket
import datetime
import sys
from random import randint
from time import sleep
from qsip.common import *
from qsip.header import *
import qsip.message
from qsip.common.utils import *
from qsip.message import *
import asyncio, logging, threading, warnings

#logging.basicConfig( level=logging.DEBUG, format='(%(threadName)-10s) %(message)s')


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # print("__CALL__", list(cls._instances.keys()), "args", args, "kwargs", kwargs )
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

class UdpReaderThread(threading.Thread):

    def __init__(self, target, transport_mgr, addresses:list, lock_handle: threading.Lock):
        super().__init__(target=target)
        self.transport_mgr = transport_mgr
        self.socket = None
        self.addressList = addresses  # Must contain at least one IpSrc
        self.thread_lock = lock_handle


    async def readData(self, my_socket: socket):
        myPort = my_socket.getsockname()
        print("Starting to listen to port:", myPort)
        await asyncio.sleep(randint(1, 3))
        count = 0
        bytesReceived = 0
        while True:
            try:
                current_loop = asyncio.get_event_loop()
                data = await current_loop.sock_recv(my_socket, MAX_UDP_DATA)
                print(f"Got data on port {myPort}")
                if self.thread_lock.acquire(blocking=True, timeout=0.5):
                    self.transport_mgr.gotMessage(data.decode())
                    self.thread_lock.release()
                else:
                    print("UDP Message discarded, thread.lock failed")
                    continue
                count = count + 1
                bytesReceived = bytesReceived + len(data)
                #print(f"We've got {count} packets, and a total of {bytesReceived} bytes")
            except BaseException as err:
                print(f'Failure processing data from socket. Type: {type(err)}, errorValue:["{err}"]')
                break

    async def handleSockets(self):
        taskList = []
        for a in self.addressList:
            my_socket = create_socket(a.proto, IP_VERSION.V4)
            if not bind_socket(my_socket, bindAddress=a.addr, bindPort=a.port):
                print("Error binding", a)
                continue
            else:
                print(f"Preping asyncio for PORT: - {a.port}")
                taskList.append(self.readData(my_socket))

        try:
            results = await asyncio.gather(taskList[0])
        except BaseException as err:
            print("AsyncIo Error", err)

    def run(self):
        print(f"THREAD-{threading.get_ident()}: We've got tp:", self.addressList, "\n")
        for p in self.addressList:
            assert p.proto == PROTOCOL.UDP, "Only UDP Ports please!"

        #event_loop = asyncio.new_event_loop()
        try:
            #event_loop.run_until_complete(self.handleSockets())
            asyncio.run(self.handleSockets())
        finally:
            print("Finally")
            #event_loop.close()

        pass


class QSipTransport(metaclass=Singleton):
    """ Transport Manager """
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
        self.count = 0


    def gotMessage(self, data: str):
        self.count = self.count + 1
        msg = None
        try:
            if Msg.isResponse(data):
                msg = Response.fromString(data)
            elif Msg.isRequest(data):
                msg = Request.fromString(data)
            else:
                print(f"Discarding bad message\n")
        except GenericSipError as err:    # TODO: Just catch/ignore ParserErrors
            print(f"Discarding message because {err}")
        print(f"Received entire message: ------------\n{msg}\n---------\n")
    def listenOnSocket(self, source: IpSrc = IpSrc("", 0, PROTOCOL.TCP)):
        pass

    def bind(self, localSources: tuple):
        assert len(localSources) > 0, "We need some ports!"
        print(f"Type is: {type(localSources)}", localSources)
        lock = threading.Lock()
        for p in localSources:
            if p.proto == PROTOCOL.UDP:
                thread_udp = UdpReaderThread(target=UdpReaderThread, transport_mgr=self, addresses=[p], lock_handle=lock)
                self._udpThreads.append(thread_udp)
                thread_udp.start()
                sleep(1.0)
            elif p.proto == PROTOCOL.TCP:
                thread_tcp = UdpReaderThread(target=UdpReaderThread, transport_mgr=self, addresses=[p])
                self._tcpThreads.append(thread_tcp)
                thread_tcp.start()
            else:
                pass
            # my_socket = create_socket(local_port.proto, IP_VERSION.V4)
            # if bind_socket(my_socket, bindAddress=local_port.addr, bindPort=local_port.port):
            # self._localBound[local_port] = socket

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
