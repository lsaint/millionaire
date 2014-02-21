# -*- coding: utf-8 -*-

from logic_pb2 import *



class Player(object):

    def __init__(self, user):
        self.uid = user.uid
        self.name = user.name
        self.role = Survivor
        self.answers = {}


    def DoAnswer(self, qid, answer):
        if self.role != Survivor:
            return False
        if self.answers.get(qid) is not None:
            return False
        self.answers[qid] = answer
        return True


    def DoRevive(self):
        if self.role != Loser:
            return False
        self.role = Reviver
        return True


    def TurnSurvivor(self):
        if self.role == Reviver:
            self.role = Survivor


    def GetAnswer(self, qid):
        return self.answers.get(qid)

