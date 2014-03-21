# -*- coding: utf-8 -*-
#

import md5, json, time, logging
from post import PostAsync, GetPostSn
from config import *


class AwardChecker(object):

    def __init__(self, race_award, personal_award):
        self.race_award = race_award
        self.personal_award = personal_award
        self.section_done = {}
        self.section_remain = {}
        self.personal_award_winners = []
        self.loadSection(race_award)


    def loadSection(self, race_award):
        if not race_award or not race_award.sections:
            return
        for section in race_award.sections:
            self.section_remain[section.id] = section


    def GetFinalId(self):
        if self.race_award:
            return self.race_award.final_id


    def GetPersonalAwardEndId(self):
        if self.personal_award:
            return self.personal_award.end_id


    # check on enter anounce state
    def CheckPersonalAward(self, qid, player):
        self.personal_award_winners = []
        if player.GetRightCount(self.personal_award.start_id,
                                self.personal_award.end_id) >= self.personal_award.bingo_time:
            self.personal_award_winners.append(player.uid)


    # check on enter anounce state
    def CheckRaceAward(self, qid, survivor_num):
        ret = self.section_done.get(qid) or []
        if len(ret) > 0 or survivor_num == 0:
            return
        for i, section in self.section_remain.items():
            if (qid >= section.trigger_id and survivor_num <= section.survivor_num) or (
                    qid == self.GetFinalId()):
                self.section_done.setdefault(qid, []).append(section)
                del self.section_remain[i]


    def GetAward(self, qid):
        return self.section_done.get(qid)


    def IsGivingPersonalAward(self):
        return self.personal_award_winners != [] and self.personal_award.bounty > 0


    # giving when leave announce state 
    def PersonalPrizeGiving(self):
        self.post2Vm(self.personal_award_winners, self.personal_award.bounty)
        return self.personal_award_winners, self.personal_award.bounty


    def RacePrizeGiving(self, qid, winners):
        sections =  self.section_done.get(qid)
        if sections is None:
            return
        if qid != self.GetFinalId():
            bounty = reduce(lambda x, y: x.bounty + y.bounty, sections)
        else:
            bounty = int(reduce(
                lambda x, y: (x.bounty * x.survivor_num) + (y.bounty * y.survivor_num),
                sections) / len(winners))
        self.post2Vm(winners, bounty)
        return bounty


    def post2Vm(self, winners, bounty):
        logging.info("WIN uids: %s, bounty: %d" % (str(winners), bounty))
        product = VM_PRODUCT
        count = len(winners)
        total_money = count * bounty
        sn = GetPostSn()
        add_time = time.strftime("%Y%m%d%H%M%S")
        desc = "L'"
        to_uid_list = []
        for uid in winners:
            to_uid_list.append({"uid": uid, "money": bounty})
        sign = md5.new("%s%d%d%d%d%s%s%s" % (product, count, total_money,
                                VM_APPID, sn, add_time, desc, VM_KEY)).hexdigest()
        dt = {"product": product,
              "appid": VM_APPID,
              "count": count,
              "total_money": total_money,
              "sn": sn,
              "to_uid_list": to_uid_list,
              "add_time": add_time,
              "desc": desc,
              "sign": sign}
        jn = json.dumps(dt)
        def done(sn, ret):
            logging.debug("post2vm ret: %s" % ret)
        PostAsync(VM_URL, jn, done, sn)



