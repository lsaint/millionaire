
import sys
sys.path.append("/Users/lsaint/go/src/millionaire/proto")

import socket, struct, time, random
from server_pb2 import *
from logic_pb2 import *
from uri import *


import gevent
from gevent import socket


LEN = 4
MY_UID = 10593000
FID = 7
TSID = 1
SSID = 2


def doPack(ins, uid=0, fid=0):
    cls = ins.__class__
    uri = CLASS2URI.get(cls)
    bin = ins.SerializeToString()

    fp = FrontendPack()
    fp.uri = uri
    fp.tsid = 1
    fp.ssid = 2
    fp.bin = bin

    if uid:
        fp.uid = uid
        fp.fid = fid

    return "%s%s" % (struct.pack("II", fp.ByteSize() + 8, 2),  fp.SerializeToString())


def register(s):
    fr = FrontendRegister()
    fr.fid = FID
    msg = "%s%s" % (struct.pack("II", fr.ByteSize() + 8, 1),  fr.SerializeToString())
    s.send(msg)


def login(s):
    pb = C2LLogin()
    pb.user.uid = MY_UID
    pb.user.name = "lSaint"
    pb.topsid = TSID
    pb.subsid = SSID
    s.send(doPack(pb, MY_UID, FID))


def NotifyMic1(s):
    gevent.sleep(1)
    pb = F2LNotifyMic1() 
    pb.user.uid = MY_UID
    topsid = TSID
    subsid = SSID
    s.send(doPack(pb))
    

def getMatch(s):
    gevent.sleep(2)
    pb = C2LMatchInfo()
    pb.user.uid = MY_UID
    s.send(doPack(pb))


def startMatch(s):
    gevent.sleep(3)
    pb = C2LStartMatch()
    pb.user.uid = MY_UID
    pb.is_warmup = False
    pb.match_id = 1
    s.send(doPack(pb))


def doPrint(body):
    fp = FrontendPack()
    fp.ParseFromString(body[LEN:])
    print "FrontendPack", fp.tsid, fp.ssid, fp.fid, fp.uid
    cls = URI2CLASS[fp.uri]
    ins = cls()
    ins.ParseFromString(fp.bin)
    print "->", fp.uri, ins.DESCRIPTOR.name, ins


def parse(data):
    if len(data) < LEN:
        return data
    (length,) = struct.unpack('I', data[:LEN])

    if len(data) >= length:
        more = data[length:]
        body = data[LEN:]   #
        doPrint(body)
        return more
    return data



def get(s):
    buf = ""
    while True:
        data = s.recv(512)
        print "recv", len(data)
        if data == "":
            print "close by peer"
            break

        #print "recv len", len(data)
        buf = "%s%s" % (buf, data)
        buf = parse(buf)



s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 40214))
jobs = [gevent.spawn(register, s),
        gevent.spawn(login, s),
        gevent.spawn(NotifyMic1, s),
        gevent.spawn(getMatch, s),
        gevent.spawn(startMatch, s),
        gevent.spawn(get, s)]

gevent.joinall(jobs)

