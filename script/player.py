# -*- coding: utf-8 -*-

import logging, time
from logic_pb2 import *



class Player(object):

    def __init__(self, user, status):
        self.uid = user.uid
        self.name = user.name
        self.coef_k = 1
        self.answers = {}
        self.ping = time.time()
        if status in (Idle, Ready):
            self.role = Survivor
        else:
            self.role = Loser


    def Reset(self):
        self.answers = {}
        self.coef_k = 1
        if self.role != Presenter:
            self.role = Survivor


    def DoAnswer(self, qid, answer):
        if self.role == Presenter or self.role == Loser:
            logging.debug("DoAnswer wrong role %s" % self.role)
            return False
        if self.answers.get(qid) is not None:
            logging.debug("DoAnswer multi answer")
            return False
        self.answers[qid] = answer
        return True


    def DoRevive(self, status):
        if self.role != Loser:
            return False
        if status == Timing:
            self.role = Survivor
        else:
            self.role = Reviver
        logging.info("DoRevive sucess uid:%d status:%d" % (self.uid, status))
        return True


    def TransformSurvivor(self):
        if self.role == Reviver:
            self.role = Survivor
            return True
        return False


    def GetAnswer(self, qid):
        return self.answers.get(qid)


    # cal on login
    def CalCoefK(self, cur_qid, right_answers, status):
        if cur_qid == 0:
            self.coef_k = 1
            return
        if len(self.answers) == 0:
            self.coef_k = cur_qid
        else:
            k = 0
            for i in range(1, cur_qid+1):
                if self.answers.get(i) != right_answers.get(i):
                    k += 1
            self.coef_k = k
        if status == Timing and cur_qid != 1:
            self.coef_k -= 1


    def CheckIncCoefK(self):
        if self.role == Survivor:
            return
        # inc presenter's k too
        self.coef_k += 1

