# -*- coding: utf-8 -*-
#
# json
# [[id, desc, [right, wrong1, wrong2, wrong3], time]...]

import json, random, logging
from post import PostAsync
from logic_pb2 import GameQuestion, A, B, C, D
from config import *

OP_HEAD = [A, B, C, D]

class QuesionPackage(object):

    def __init__(self):
        self.id2question = {}
        self.id2rightanswer = {}


    def Load(self, pid, func):
        def done(sn, ret):
            self.parseJson(ret)
            func()
        PostAsync("%s%s%s" % (URL_OP, SUF_QPACK, pid), "", done)


    def parseJson(self, jn):
        logging.info("LoadQuestion: %s" % jn)
        global OP_HEAD
        lt = json.loads(jn)
        for q in lt:
            op = q[2]                           # options
            right_answer = op[0]
            random.shuffle(op)
            gq = GameQuestion()
            gq.id = q[0]                        # id
            gq.question = q[1]                  # question desc
            gq.options.extend(op)
            gq.count_time = q[3]                # count_time
            self.id2question[gq.id] = gq

            for i in range(len(OP_HEAD)):
                if op[i] == right_answer:
                    self.id2rightanswer[gq.id] = OP_HEAD[i]


    def GetQuestionCount(self):
        return len(self.id2question)


    def GetQuestion(self, qid):
        return self.id2question.get(qid)


    def GetRightAnswer(self, qid):
        return self.id2rightanswer.get(qid)

