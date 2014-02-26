# -*- coding: utf-8 -*-

from logic_pb2 import A, B, C, D, UserAnswer
from config import TOPN

class StatiMgr(object):

    def __init__(self, right_answer):
        self.abcd2count = {A:0, B:0, C:0, D:0}
        self.time2player = {}
        self.right_answer = right_answer
        self.topn = []


    def OnAnswer(self, player, abcd, elapse):
        self.abcd2count[abcd] += 1
        self.time2player[elapse] = player
        if len(self.topn) < TOPN and self.right_answer == abcd:
            ua = UserAnswer()
            ua.user.name = player.name
            ua.elapse = elapse
            self.topn.append(ua)


    def GetDistribution(self):
        return [self.abcd2count[A], self.abcd2count[B],
                self.abcd2count[C], self.abcd2count[D]]


    def GetTopN(self):
        return self.topn



