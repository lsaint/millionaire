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
        for i, section in range race_award_section:
            self.section_remain[section.id] = section


    def Check(self, qid, survivor_num):
        return None


    def checkRaceAward(self, qid, survivor_num):
        ret = []
        for i, section in self.section_remain.items():
            if qid >= section_done.trigger_id and survivor_num <= section.survivor_num:
                ret.append(section)
                self.section_done[i] = section
                del self.section_remain[i]
        return ret

