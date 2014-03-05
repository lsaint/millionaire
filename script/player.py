# -*- coding: utf-8 -*-

import logging
from logic_pb2 import *



class Player(object):

    def __init__(self, user):
        self.uid = user.uid
        self.name = user.name
        self.role = Survivor
        self.first_lose_id = None
        self.answers = {}
        self.ping = 0


    def Reset(self):
        self.answers = {}
        self.first_lose_id = None
        if self.role != Presenter:
            self.role = Survivor


    def DoAnswer(self, qid, answer):
        if self.role != Survivor:
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


