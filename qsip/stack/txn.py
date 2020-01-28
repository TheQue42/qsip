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


class TimerEntry(NamedTuple):
    initial: int = 0.5
    max: int = 32.0


class TxnTimer:

    def __init__(self, name: str, start: int, receiver: Txn):
        self.totalTime = 0
        self.timerValue = TimerEntry(start, 32.0)
        self.current_value = self.timerValue.start
        self._timer_receiver = receiver
        self.timer_name = name
        self.id = genRandomIntString(32)
        self.t = None

    def getT1(self):
        return 0.5

    def getTimerDefaultValue(self, timer_name: str):
        return self.timerValues.start  # Based on Name

    def startTimer(self, *args, **kwargs):
        assert self.t is None, "Timer already running!"
        self.t = Timer(self.current_value, self.timerPop, [self.id] + args, **kwargs)
        self.t.start()

    def timerPop(self, timer_id: str, *args, **kwargs):
        self.totalTime += self.current_value
        if self.totalTime >= self.timerValue.max:
            self._timer_receiver.transactionTimeout(*args, **kwargs)
        else:
            self._timer_receiver.timerPop(*args, **kwargs)
            self.backoff_double(self.current_value)
            self.restartTimer()

    def backoff_double(self, timer_name):
        self.current_value = self.current_value * 2  # TODO: Capoff based on name

    def restartTimer(self):
        self.t.cancel()
        self.t = Timer(self.current_value, self.timerPop, self.id)

    def stop(self):
        if self.t is not None:
            self.t.cancel()
            self.t = None


class TxnUser:

    def __init__(self):
        pass

    def txnFailed(self, *, txn: Txn, reason: str = ""):
        assert False, "Should be overridden by UA"

    def txnTerminated(self, txn: Txn, reason: str = ""):
        assert False, "Should be overridden by UA"


class Txn:

    def __init__(self, sender: TxnUser):
        self.transportMgr = QSipTransport()
        self._id = genRandomIntString(24)
        self._local = ""
        self._socket, self._local_addr, self._local_port = (0, 0, 0)
        self._tu = sender

    def Id(self):
        return self._id


class ClientTxn(Txn):

    def __init__(self, sip_request: Request, sender: TxnUser):
        self._next_hop = ""
        self._request = sip_request
        super().__init__(sender)

    def restartClientTimer(self):
        self.restartTimer()

    def restartTimer(self):
        assert False, "Must be overridden by INVITE and NonINVITE"

    def timerPop(self, which_timer, timerValue: int):

        # TODO: Check which timer, maxTimer value. Delegate to subclass
        print("Pop", timerValue, which_timer, "self", self)
        if timerValue > 16:
            self.failClientTxn()  # TODO: add Reason
            return

        if self.sendOnSocket(self._request, self._socket, self._next_hop):
            self.restartClientTimer()
        else:
            self.failClientTxn()  # TODO: add Reason

    def sendOnSocket(self, msg, sock, next_hop) -> bool:
        # print("======== Sending ============", datetime.datetime.now())
        print(str(msg))
        # print("======== Sending ============")
        bytesToSend = str(msg).encode()
        # TODO: Check socket is valid? getpeername, getsockname?

        result = sock.sendto(bytesToSend, (next_hop.addr, next_hop.port))

        if result != len(bytesToSend):
            sock.close()
            print("Failed Sending Entire messages")
            return False

        return True

    def failClientTxn(self):
        self._tu.txnFailed(txn=self, reason="TxnTimeout")


class InviteClientTxn(ClientTxn):
    def __init__(self, sip_request: Request, sender: TxnUser):
        super().__init__(sip_request, sender)

    def restartTimer(self):
        pass  # TODO:


class NonInviteClientTxn(ClientTxn):
    def __init__(self, sip_request: Request, sender: TxnUser):
        # self._local = ""
        # self._next_hop = ""
        # self._socket, self._local_addr, self._local_port = (0,0,0)
        super().__init__(sip_request, sender)

    def restartTimer(self):
        t = Timer(self.timerValue, self.timerPop,
                  [111, self.timerValue])  # TODO: Which timer, Values, MaxValues, Aggregated Values
        self.timerValue = self.timerValue * 2
        t.start()

    def send(self, local, remote):
        self._local = local
        self._next_hop = remote
        self._socket, self._local_addr, self._local_port = self.transportMgr.getUdpSocket(
            self._next_hop)  # TODO: Use LOCAL

        if self._local_port == 0 or self._socket is None:
            print("Failed binding/connecting")
            self.failClientTxn()
            return

        self._request.setSocketInfo(self._local_addr, self._local_port)
        self.timer = TxnTimer("Timer_A", 0.5, 32, self)
        self.timer.startTimer()
        # initTimer


class ServerTxn:
    pass

# queueEntry = dict()
##queueEntry["msg"] = msgRequest
# queueEntry["next_hop"] = next_hop
# queueEntry["socket"] = current_socket
