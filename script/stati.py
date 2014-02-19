# -*- coding: utf-8 -*-

from logic_pb2 import A, B, C, D


class StatiMgr(object):

    def __init__(self):
        self.abcd2count = {A:0, B:0, C:0, D:0}
        self.time2player = {}


    def OnAnswer(self, player, abcd, elapse):
        self.abcd2count[abcd] += 1
        self.time2player[elapse] = player


    def GetDistribution():
        return [self.abcd2count[A], self.abcd2count[B],
                self.abcd2count[C], self.abcd2count[D]]
