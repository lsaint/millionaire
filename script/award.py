# -*- coding: utf-8 -*-
#

import md5, json, time
from post import PostAsync, GetPostSn
from config import *


class AwardChecker(object):

    def __init__(self, race_award, personal_award):
        self.race_award = race_award
        self.personal_award = personal_award
        self.section_done = {}
        self.section_remain = {}
        self.loadSection(race_award)


    def loadSection(self, race_award):
        if not race_award or not race_award.sections:
            return
        for section in race_award.sections:
            self.section_remain[section.id] = section


    def GetFinalId(self):
        if self.race_award:
            return self.race_award.final_id


    def checkFinalAward(self, qid):
        if self.race_award and qid == self.race_award.final_id:
            return self.section_remain
        return []


    def checkRaceAward(self, qid, survivor_num):
        ret = self.section_done.get(qid) or []
        if len(ret) > 0:
            return
        for i, section in self.section_remain.items():
            if qid >= section.trigger_id and survivor_num <= section.survivor_num:
                self.section_done.setdefault(qid, []).append(section)
                del self.section_remain[i]


    def Check(self, qid, survivor_num):
        ret = self.checkFinalAward(qid)
        if not ret:
            self.checkRaceAward(qid, survivor_num)


    def GetAward(self, qid):
        return self.section_done.get(qid)


    def PrizeGiving(self, qid, winners):
        sections =  self.section_done.get(qid)
        if sections is None:
            return
        bounty = 0
        for section in sections:
            bounty += section.bounty
        self.post2Vm(winners, bounty)
        return bounty


    def post2Vm(self, winners, bounty):
        product = VM_PRODUCT
        count = len(winners)
        total_money = count * bounty
        sn = GetPostSn()
        add_time = time.strftime("%Y%m%d%H%M%S")
        desc = "L'"
        to_uid_list = []
        for uid in winners:
            to_uid_list.append({"uid": uid, "money": bounty})
        sign = md5.new("%s%d%d%d%s%s%s" % (product,
                        count, total_money, sn, add_time, desc, VM_KEY)).hexdigest()
        dt = {"product": product,
              "count": count,
              "total_money": total_money,
              "sn": sn,
              "to_uid_list": to_uid_list,
              "add_time": add_time,
              "desc": desc,
              "sign": sign}
        jn = json.dumps(dt)
        def done(sn, ret):
            print "post2vm ret:", ret
        PostAsync(VM_URL, jn, done, sn)



