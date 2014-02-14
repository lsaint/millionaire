# -*- coding: utf-8 -*-
import time

class Timer(object):
    TimerDict = {}    # {tid:[time, fun, args]}
    Index = 0

    # 记录本次实例化后创建的timerid
    def __init__(self):
        self._TimerIdList = []

    # 释放本次实例化后的所有timer
    def ReleaseTimer(self):
        for idx in self._TimerIdList[:]:
            self.KillTimer(idx)
            self._TimerIdList.remove(idx)

    @classmethod
    def Update(cls):
        if len(Timer.TimerDict) == 0:
            return
        t = time.time()
        for tid, lt in Timer.TimerDict.items():
            if t >= lt[0]:
                cls.KillTimer(tid)
                apply(lt[1], lt[2])



    def SetTimer(self, sec, callbackfun, *args):
        Timer.Index += 1
        dotime = sec + time.time() 
        Timer.TimerDict[Timer.Index] = [dotime, callbackfun, args]
        self._TimerIdList.append(Timer.Index)

        return Timer.Index


    @classmethod
    def KillTimer(cls, tid):
        if Timer.TimerDict.has_key(tid):
            del Timer.TimerDict[tid]


