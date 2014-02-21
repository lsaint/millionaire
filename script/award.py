# -*- coding: utf-8 -*-
#
# json
# [start, refuse_revive, final, [[alive1, bounty1]...], [start, end, times, bountry]]




class AwardChecker(object):

    def __init__(self, race_award, personal_award):
        self.race_award = race_award
        self.personal_award = personal_award
        self.loadSection(race_award)
        self.section_done = {}
        self.section_remain = {}


    def loadSection(self, race_award):
        if not race_award:
            return
        for i, section in race_award:
            self.section_remain[section.id] = section


    def GetFinalId(self):
        if self.race_award:
            return self.race_award.final_id


    def checkFinal(self, qid):
        if self.race_award and qid == self.race_award.final_id:
            return self.section_remain
        return []


    def checkRaceAward(self, qid, survivor_num):
        ret = self.section_done.get(qid) or []
        if len(ret) > 0:
            return ret
        for i, section in self.section_remain.items():
            if qid >= section_done.trigger_id and survivor_num <= section.survivor_num:
                ret.append(section)
                self.section_done.setdefault(qid, section)
                del self.section_remain[i]
        return ret


    def Check(self, qid, survivor_num):
        ret = self.checkFinal(qid)
        if not ret:
            return self.checkRaceAward(qid, survivor_num)


    def PrizeGiving(self, qid):
        if self.section_done.get(qid) is None:
            return
        print "section giving"


