import socket
from enum import Enum

class PROTOCOL(Enum):
    TCP = 0
    UDP = 1
    SCTP = 2


class IP_VERSION(Enum):
    V6 = 0
    V4 = 1

def create_socket(proto : PROTOCOL, ip_version : IP_VERSION) -> socket:
    """Connect/authenticate to SIP Server."""
    # TODO: AF_INET6, udp

    if proto == PROTOCOL.UDP and ip_version == IP_VERSION.V4:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as err:
            _LOGGER.exception("Socket creation failed with error %s" % (err))
    else:
        return None ### TQ-TODO: v6, tcp

    print("Socket successfully created: FileNo: ", s.fileno())

    if proto == PROTOCOL.TCP:
        try:
            # TQ-CHECK: Strange undefined symbol SO_REUSEPORT, for python-3.8 on win10?
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            print("SetSockOpt(SO_REUSEPORT)")
        except socket.error as err:
            _LOGGER.exception("setsockOpt(SO_REUSEPORT) error %s" % (err))

        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("SetSockOpt(SO_REUSEADDR)")
        except socket.error as err:
            _LOGGER.exception("setsockOpt(SO_REUSEADDR) error %s" % (err))

    return s


def bind_socket(my_socket: socket, *, bindAddress ="", bindPort = 0) -> bool:
    """"""
    try:    ### TODO: Acquire local-IP. Will be 172.x in docker...
        print(f"Trying to bind socket({my_socket.fileno()}) with: [{bindAddress}] and Port: [{bindPort}]")
        ### TQ-TODO: IpV6 will expect a 4-tuple.
        my_socket.bind((bindAddress, 0))
    except socket.error as err:
        print("Socket bind failed with error %s" % (err))
        return False
    print("Socket bound successfully: ", my_socket.getsockname())
    return True


def connect_socket(my_socket : socket, dst_addr : str, dst_port : int):
    """This is needed to get the local IP and Port"""

    print(f"Will (attempt to) connect with: socket({my_socket.fileno()}), towards {dst_addr}, {dst_port}")
    try:
        my_socket.connect((dst_addr, dst_port))
    except socket.error as err:
        print("Socket connect failed: ", my_socket, " ", err)
        return "", 0

    (localAddr, localPort) = my_socket.getsockname()
    return (localAddr, localPort)
