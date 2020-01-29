from __future__ import annotations
import socket
import datetime
import sys
from dataclasses import dataclass

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

TIMER_T1 = 0.5
TIMER_T1_64 = 32.0
TIMER_C = 180
TIMER_T4 = 4.0
TIMER_FAILSAFE_MAX = 64.0


class TxnTimer:

    def getStartValue(self, timer_name: str, proto: PROTOCOL = PROTOCOL.UDP):
        value = 0
        if re.search('timer[_-][AEG]', timer_name, re.IGNORECASE):
            return self.timer_t1
        elif re.search("timer[_-][BFH]", timer_name, re.IGNORECASE):
            return self.timer_t1 * 64
        elif re.search("timer[_-]C", timer_name, re.IGNORECASE):
            return TIMER_C
        elif re.search("timer[_-]D", timer_name, re.IGNORECASE):
            value = 32.0 if proto == PROTOCOL.UDP else 0
        elif re.search("(timer[_-])[IK]", timer_name, re.IGNORECASE):
            value = TIMER_T4 if proto == PROTOCOL.UDP else 0
        elif re.search("(timer[_-])J", timer_name, re.IGNORECASE):
            value = self.timer_t1*64 if proto == PROTOCOL.UDP else 0
        return value

    def __init__(self, timer_name: str, receiver: Txn, **kwargs):
        self.totalTime = 0
        self._timer_receiver = receiver
        self._timer_name = timer_name  # Timer_A|F, etc
        self._id = genRandomIntString(32)
        if "timer_t1" in kwargs.keys():
            self.timer_t1 = kwargs["timer_t1"]
        else:
            self.timer_t1 = TIMER_T1
        self.current_value = self.getStartValue(self._timer_name)
        if re.search("timer[_-]E", timer_name, re.IGNORECASE):
            self.capOff = TIMER_T4
        else:
            self.capOff = TIMER_T1_64   # Timer A/E doesnt really have cap off, its stopped by B/F
        self.t = None

    def startTimer(self, **kwargs):
        assert self.t is None, "Timer already running!"
        if "timeout" in kwargs.keys():
            self.current_value = kwargs["timeout"]
        print("Starting timer", self._timer_name, "Initial:", self.current_value)
        self.t = Timer(self.current_value, self.timerPop, [self._id], kwargs)
        self.t.start()

    def timerPop(self, timer_id: str, **kwargs):
        self.totalTime += self.current_value
        if self.totalTime >= TIMER_FAILSAFE_MAX:
            self._timer_receiver.timeoutMaxReached(self, timer_id, **kwargs)
        else:
            self._timer_receiver.timerPop(self, self._timer_name, **kwargs)

    def backoff_double(self, timer_name):
        self.current_value = self.current_value * 2 if self.current_value < self.capOff else self.capOff

    def restartTimer(self, **kwargs):
        print("Restarting", self._timer_name, self.current_value)
        self.t.cancel()
        self.backoff_double(self._timer_name)
        self.t = Timer(self.current_value, self.timerPop, [self._id], kwargs)
        self.t.start()

    def stop(self):
        if self.t is not None:
            print("Stopping", self._timer_name, self.__class__)
            self.t.cancel()
            self.t = None

    def id(self) -> str:
        return self._id


class TxnUser:

    def __init__(self):
        pass

    def txnFailed(self, *, txn: Txn, reason: str = "", **kwargs):
        assert False, "Should be overridden by UA"

    def txnTerminated(self, txn: Txn, reason: str = "", **kwargs):
        assert False, "Should be overridden by UA"


class Txn:

    def __init__(self, sender: TxnUser):
        self.transportMgr = QSipTransport()
        self._id = genRandomIntString(24)
        self._local = ""
        self._socket, self._local_addr, self._local_port = (0, 0, 0)
        self._tu = sender

    def id(self):
        return self._id

    def timerPop(self, timer: TxnTimer, timer_name: str, *args, **kwargs):
        assert False, "Please Override"

    def timeoutMaxReached(self, timer: TxnTimer, timer_name: str, **kwargs):
        print("Timer:", timer, timer_name)
        assert False, "Forgotten Timer"

class ClientTxn(Txn):

    def __init__(self, sip_request: Request, sender: TxnUser, **kwargs):
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
        super().__init__(sender, **kwargs)

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
            self.failClientTxn("Transport Error - Failed acquiring socket")
            return
        self._request.setSocketInfo(self._local_addr, self._local_port)
        self._request.getTopHeader(HeaderEnum.VIA).initBranch(self.id())
        if sendOnSocket(self._request, self._socket, self._next_hop):
            self.startTxnTimer(self.timer_t1)   # Uses subclass client txn
        else:
            self.failClientTxn("Transport Error")  # TODO: add Reason

    def timerPop(self, timer: TxnTimer, timer_name: str, **kwargs):

        print("Timer Pop", timer_name, timer.current_value)
        
        if timer == self.timerRetransmit and self.shouldRetransmit(self):
        
            if sendOnSocket(self._request, self._socket, self._next_hop):
                timer.restartTimer(pelle="Hejsan")  # Will auto-double if needed
            else:
                self.failClientTxn("Transport Error")  # TODO: add Reason
        else:
            assert timer == self.timerTxnTimeout
            self.timerRetransmit.stop()
            self.failClientTxn("TxnTimeout", **kwargs)

    def failClientTxn(self, reason: str = "TxnTimeout", **kwargs):
        self._tu.txnFailed(txn=self, reason=reason, **kwargs)


class InviteClientTxn(ClientTxn):

    def __init__(self, sip_request: Request, sender: TxnUser, **kwargs):
        super().__init__(sip_request, sender, **kwargs)

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

    def __init__(self, sip_request: Request, sender: TxnUser, **kwargs):
        super().__init__(sip_request, sender, **kwargs)

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
