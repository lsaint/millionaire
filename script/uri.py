# -*- coding: utf-8 -*-


from logic_pb2 import *
from server_pb2 import *


URI2CLASS_ROOM = {
        104     :   C2LLogin,
        110     :   F2LNotifyMic1,

        100     :   C2LMatchInfo,
        101     :   L2CMatchInfoRep,
        102     :   C2LStartMatch,
        103     :   L2CNotifyMatchInfo,
        105     :   L2CLoginRep,
        106     :   C2LTimeSync,
        107     :   L2CTimeSyncRep,
        108     :   C2LPing,
        109     :   L2CPingRep,
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
        134     :   L2CAnswerQuestionRep,
        135     :   L2FNotifyBalanceChange,
        136     :   L2FSyncGameRoomInfos,
        137     :   L2CNotifyBillboard,
        138     :   L2CNotifyPreload,
        147     :   C2LChangeGameMode,
        148     :   L2CNotifyGameMode,
}

URI2CLASS_GLOBAL = {
        104     :   C2LLogin,
        110     :   F2LNotifyMic1,
        99      :   N2SRegister,
}

URI2CLASS_CAPTURE_FLAG = {
        104     :   C2LLogin,
        139     :   C2LStartCaptureFlag,
        140     :   L2CStartCaptureFlagRep,
        141     :   L2CNotifyFlagStatus,
        142     :   F2LCaptureAction,
        143     :   L2CNotifyFlagMesssage,
        144     :   F2LFirstBlood,
        145     :   L2FFirstBloodRep,
        146     :   L2CNotifyMoneyChange,
        147     :   C2LChangeGameMode,
}

URI2CLASS = {}
URI2CLASS.update(URI2CLASS_ROOM)
URI2CLASS.update(URI2CLASS_GLOBAL)
URI2CLASS.update(URI2CLASS_CAPTURE_FLAG)

CLASS2URI = {}
for uri, proto in URI2CLASS.items():
    CLASS2URI[proto] = uri

