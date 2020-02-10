from __future__ import annotations
from qsip.common import *
#from qsip.common.utils import *
from qsip.stack.transport import *
from threading import Timer


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
        #print("Restarting", self._timer_name, self.current_value)
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
