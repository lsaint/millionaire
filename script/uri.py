# -*- coding: utf-8 -*-


from logic_pb2 import *
from server_pb2 import *


URI2CLASS = {
        100     :   C2LMatchInfo,
        101     :   L2CMatchInfoRep,
        102     :   C2LStartMatch,
        103     :   L2CNotifyMatchInfo,
        104     :   C2LLogin,
        105     :   L2CLoginRep,
        106     :   C2LTimeSync,
        107     :   L2CTimeSyncRep,
        108     :   C2LPing,
        109     :   L2CPingRep,
        110     :   F2LNotifyMic1,
        111     :   C2LNextStep,
        112     :   L2CNextStepRep,
        113     :   L2CNotifyPresenterChange,
        114     :   L2CNotifyReadyStatus,
        115     :   L2CNotifyTimingStatus,
        116     :   L2CNotifyTimeupStatus,
        117     :   C2LAnswerQuestion,
        118     :   L2CNotifyStatisticsStatus,
        119     :   L2CNotifyAnswerStatus,
        120     :   L2CNotifyAnnounceStatus,
        121     :   L2CNotifyAwardStatus,
        122     :   L2CNotifyEndingStatus,
        123     :   C2LRevive,
        124     :   F2CReviveRep,
        125     :   F2LNotifyRevive,
        126     :   L2FNotifyRevieRep,
        127     :   L2CNotifyIdleStatus,
        128     :   L2CNotifyPreview,
        129     :   L2CNotifyGameQuestion,
        130     :   L2CNotifySituation,
        131     :   L2FReviveRep,
        132     :   C2LLogout,
        133     :   L2CNotifyPersonalAward,
}

CLASS2URI = {}
for uri, proto in URI2CLASS.items():
    CLASS2URI[proto] = uri

