# -*- coding: utf-8 -*-

import logging, time
from logic_pb2 import *



class Player(object):

    def __init__(self, user):
        self.uid = user.uid
        self.name = user.name
        self.role = Survivor
        self.coef_k = 1
        self.answers = {}
        self.ping = time.time()


    def Reset(self):
        self.answers = {}
        self.coef_k = 1
        if self.role != Presenter:
            self.role = Survivor


    def DoAnswer(self, qid, answer):
        if self.role != Survivor or self.role != Reviver:
            logging.debug("DoAnswer wrong role")
            return False
        if self.answers.get(qid) is not None:
            logging.debug("DoAnswer multi answer")
            return False
        self.answers[qid] = answer
        return True


    def DoRevive(self):
        if self.role != Loser:
            return False
        self.role = Reviver
        return True


    def TransformSurvivor(self):
        if self.role == Reviver:
            self.role = Survivor


    def GetAnswer(self, qid):
        return self.answers.get(qid)


    # cal on login
    def CalCoefK(self, cur_qid, right_answers):
        if len(self.answers) == 0:
            self.coef_k = cur_qid
            return

        k = 0
        for i in range(1, cur_qid+1):
            if self.answers.get(i) != right_answers.get(i):
                k += 1
        self.coef_k = k


    def CheckIncCoefK(self):
        if self.role == Survivor:
            return
        # inc presenter's k too
        self.coef_k += 1

