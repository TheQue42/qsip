from __future__ import annotations
import socket
import datetime
import sys
from dataclasses import dataclass
from qsip.stack.TxnTimer import *
from qsip.common import *
from qsip.header import *
from qsip.common.utils import *
from qsip.message import *
from qsip.stack.transport import *
from threading import Timer


"""
Timer    Value            Section               Meaning
----------------------------------------------------------------------
T1       500ms default    Section 17.1.1.1     RTT Estimate
T2       4s               Section 17.1.2.2     The maximum retransmit interval for non-INVITE req and INVITE rsp
T4       5s               Section 17.1.2.2     Maximum duration a message will remain in the network
Timer A  initially T1     Section 17.1.1.2     INVITE request retransmit interval, for UDP only
Timer B  64*T1            Section 17.1.1.2     INVITE transaction timeout timer
Timer C  > 3min           Section 16.6         proxy INVITE transaction timeout
Timer D  > 32s for UDP    Section 17.1.1.2     Wait time for response retransmits
Timer E  initially T1     Section 17.1.2.2     non-INVITE request retransmit interval, UDP only
Timer F  64*T1            Section 17.1.2.2     non-INVITE transaction timeout timer
Timer G  initially T1     Section 17.2.1       INVITE response retransmit interval
Timer H  64*T1            Section 17.2.1       Wait time for ACK receipt
Timer I  T4 for UDP       Section 17.2.1       Wait time for ACK retransmits
Timer J  64*T1 for UDP    Section 17.2.2       Wait time for non-INVITE request retransmits
Timer K  T4 for UDP       Section 17.1.2.2     Wait time for response retransmits
    """


class TxnUser:
    """Interface for Transaction User, i.e The UA layer"""
    def __init__(self):
        pass

    def txnFailed(self, *, txn: Txn, reason: str = "", **kwargs):
        assert False, "Should be overridden by UA"

    def txnTerminated(self, txn: Txn, reason: str = "", **kwargs):
        assert False, "Should be overridden by UA"

class QTxnMgr(metaclass=Singleton):
    """ Txn Manager """

    def __init__(self, **kwargs):
        print("Initializing Singleton Txn Manager")
        self._txn_storage = dict()  # Keyed on ;branch?

    def matchTxn(self, txnId: str) -> Txn:
        if txnId in self._txn_storage.keys():
            return self._txn_storage[txnId]
        else:
            return None, None

    def addTxn(self, txn: Txn, tu: TxnUser):
        self._txn_storage[txn.id()] = txn, tu

    def sendRequest(self, tu: TxnUser,
                    req: Request,
                    source: IpSrc, next_hop: IpDst,
                    stateless: bool = False, **kwargs):

        if req._method != "INVITE":
            txn = NonInviteClientTxn(req, timer_t1=0.1)
        else:
            txn = InviteClientTxn(req)

        self.addTxn(txn, tu)
        txn.sendRequest(source, next_hop)

    def send_failure(self, txn: Txn, reason: str = ""):
        foundTxn, txnOwner = self.matchTxn(txn.id())
        if foundTxn is not NonInviteClientTxn:
            print("Transaction Failed With", reason, "Id:", foundTxn.id(), "caller:", txnOwner)
            txnOwner.txnFailed(txn, reason)
        else:
            print("Stateless Request Failed", reason, "Id:", foundTxn.id())
        sys.exit()


class Txn:
    """Top Level SIP Transaction"""

    def __init__(self, **kwargs):
        self.transportMgr = QSipTransport()
        self.txnMgr = QTxnMgr()
        if "branch" in kwargs.keys():
            self._txnId = kwargs["branch"]
            kwargs.pop("branch")
        else:
            self._txnId = genRandomIntString(24)
        self._local = ""
        self._socket, self._local_addr, self._local_port = (0, 0, 0)

    def id(self):
        return self._txnId

    def timerPop(self, timer: TxnTimer, timer_name: str, *args, **kwargs):
        assert False, "Please Override"

    def timeoutMaxReached(self, timer: TxnTimer, timer_name: str, **kwargs):
        print("Timer:", timer, timer_name)
        assert False, "Forgotten Timer"


class ClientTxn(Txn):

    def __init__(self, sip_request: Request, **kwargs):
        self._next_hop = ""
        self._request = sip_request
        self.timer = None
        self.timerRetransmit = 0
        self.timerTxnTimeout = 0
        if "timer_t1" in kwargs.keys():
            self.timer_t1 = kwargs["timer_t1"]
            kwargs.pop("timer_t1")
        else:
            self.timer_t1 = TIMER_T1
        topVia = sip_request.getTopHeader(HeaderEnum.VIA)
        preEncodedBranch = topVia.getBranch()
        if preEncodedBranch is not None and preEncodedBranch != "":
            super().__init__(branch=preEncodedBranch, **kwargs)
        else:
            super().__init__(**kwargs)

    def startTxnTimer(self, timer_t1: int, **kwargs):
        assert False, "MUST be Overridden"

    def shouldRetransmit(self, **kwargs):
        assert False, "MUST be Overridden"

    def sendRequest(self, local, remote):
        self._local = local
        self._next_hop = remote
        self._socket, self._local_addr, self._local_port = self.transportMgr.getUdpSocket(self._next_hop)

        if self._local_port == 0 or self._socket is None:
            print("Failed binding/connecting")
            self.send_failure("Transport Error - Failed acquiring socket")
            return
        self._request.setSocketInfo(self._local_addr, self._local_port)
        topVia = self._request.getTopHeader(HeaderEnum.VIA)
        if topVia.getBranch():
            print("Found:", topVia)
        else:
            topVia.initBranch(self.id()) # TODO Stateless Via branch ?

        if sendOnSocket(self._request, self._socket, self._next_hop):
            self.startTxnTimer(self.timer_t1)   # Uses subclass client txn
        else:
            self.send_failure("Transport Error")  # TODO: add Reason

    def timerPop(self, timer: TxnTimer, timer_name: str, **kwargs):
        """Handles timer pop of Timer A/E and Timer B/F for INVITE and nonINVITE.
           Subclass check will verify is retransmission should(still) be done.
        """
        if timer == self.timerRetransmit and self.shouldRetransmit():
            if sendOnSocket(self._request, self._socket, self._next_hop):
                timer.restartTimer()  # Will auto-double if needed
            else:
                self.failClientTxn("Transport Error")  # TODO: add Reason
        else:
            assert timer == self.timerTxnTimeout
            self.timerRetransmit.stop()
            self.failClientTxn("TxnTimeout", **kwargs)

    def failClientTxn(self, reason: str = "TxnTimeout", **kwargs):
        self.txnMgr.send_failure(txn=self, reason=reason, **kwargs)


class InviteClientTxn(ClientTxn):

    def __init__(self, sip_request: Request, **kwargs):
        super().__init__(sip_request, **kwargs)

    def restartTimer(self):
        pass  # TODO:

    def shouldRetransmit(self, **kwargs):
        # TODO If ! 1xxReceived
        return True
    
    def startTxnTimer(self, timer_t1: int, **kwargs):
        self.timerRetransmit = TxnTimer("Timer_A", self)
        self.timerTxnTimeout = TxnTimer("Timer_B", self)
        self.timerRetransmit.startTimer()
        self.timerTxnTimeout.startTimer()


class NonInviteClientTxn(ClientTxn):

    def __init__(self, sip_request: Request, **kwargs):
        super().__init__(sip_request, **kwargs)

    def shouldRetransmit(self, **kwargs):
        return True

    
    def startTxnTimer(self, timer_t1: int, **kwargs):
        self.timerRetransmit = TxnTimer("Timer_E", self, timer_t1=timer_t1)
        self.timerTxnTimeout = TxnTimer("Timer_F", self, timer_t1=timer_t1)
        self.timerRetransmit.startTimer()
        self.timerTxnTimeout.startTimer()


class ServerTxn:
    pass

# queueEntry = dict()
##queueEntry["msg"] = msgRequest
# queueEntry["next_hop"] = next_hop
# queueEntry["socket"] = current_socket
