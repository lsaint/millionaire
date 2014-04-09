# -*- coding: utf-8 -*-

import logging
from logic_pb2 import A, B, C, D, UserAnswer
from config import TOPN

class StatiMgr(object):

    def __init__(self, qid, right_answer):
        self.qid = qid
        self.abcd2count = {A:0, B:0, C:0, D:0}
        self.right_answer = right_answer
        self.topn = []


    def OnAnswer(self, player, abcd, elapse):
        self.abcd2count[abcd] += 1
        if len(self.topn) < TOPN and self.right_answer == abcd:
            ua = UserAnswer()
            ua.user.uid = player.uid
            ua.user.name = player.name
            ua.answer.id = self.qid
            ua.elapse = elapse
            self.topn.append(ua)


    def GetDistribution(self):
        return [self.abcd2count[A], self.abcd2count[B],
                self.abcd2count[C], self.abcd2count[D]]


    def LogDistribution(self):
        total = reduce(lambda x, y: x+y, self.GetDistribution())
        right = self.abcd2count[right_answer]
        logging.info("S-ANS %d %d %d %d" % (qid, total, right, total-right))


    def GetTopN(self):
        return self.topn



