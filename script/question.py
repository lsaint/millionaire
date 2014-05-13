# -*- coding: utf-8 -*-
#
# json
# [[id, desc, [right, wrong1, wrong2, wrong3], time]...]

import json, random, logging
from post import PostAsync
from logic_pb2 import GameQuestion, A, B, C, D, TXT, PIC, L2CNotifyPreload 
from config import *

OP_HEAD = [A, B, C, D]

class QuesionPackage(object):

    def __init__(self):
        self.id2question = {}
        self.id2rightanswer = {}
        self.pb_preload = None 


    def Load(self, pid, func):
        def done(sn, ret):
            ok = self.parseJson(ret)
            func(sn, ok)
        return PostAsync("%s%s%s" % (URL_OP, SUF_QPACK, pid), "", done)


    def parseJson(self, jn):
        #logging.info("LoadQuestion: %s" % jn)
        global OP_HEAD
        try:
            lt = json.loads(jn)
        except:
            logging.error("load question error: %s" % jn)
            return False
        for q in lt:
            op = q[2]                           # options
            right_answer = op[0]
            random.shuffle(op)
            gq = GameQuestion()
            gq.id = q[0]                        # id
            gq.question = q[1]                  # question desc
            gq.options.extend(op)
            gq.count_time = q[3]                # count_time
            gq.type = q[4]
            gq.pic_url = q[5]
            self.id2question[gq.id] = gq

            for i in range(len(OP_HEAD)):
                if op[i] == right_answer:
                    self.id2rightanswer[gq.id] = OP_HEAD[i]

            if gq.type == PIC:
                if not self.pb_preload:
                    self.pb_preload = L2CNotifyPreload()
                q = self.pb_preload.pre.add()
                q.id  = gq.id
                q.pic_url = gq.pic_url
                logging.debug("preloading %d" % q.id)

        return True


    def GetQuestionCount(self):
        return len(self.id2question)


    def GetQuestion(self, qid):
        return self.id2question.get(qid)


    def GetPreloadQuestions(self):
        return self.pb_preload


    def GetRightAnswer(self, qid):
        return self.id2rightanswer.get(qid)

