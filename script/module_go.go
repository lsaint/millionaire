package script

import (
    "fmt"
    "github.com/qiniu/py"

    pb "code.google.com/p/goprotobuf/proto"
    "millionaire/proto"
)


type GoModule struct {
    sendChan        chan *proto.GateOutPack
}

func NewGoModule(out chan *proto.GateOutPack) *GoModule {
    mod := &GoModule{sendChan: out}
    return mod
}

func (this *GoModule) Py_SendMsg(args *py.Tuple) (ret *py.Base, err error) {
    var tsid, ssid, uri, action int
    var sbin string
    err = py.Parse(args, &tsid, &ssid, &uri, &sbin, &action)
    if err != nil {
        fmt.Println("SendMsg err", err)
        return
    }
    this.sendChan <- &proto.GateOutPack{Tsid: pb.Uint32(uint32(tsid)), 
                                        Ssid: pb.Uint32(uint32(ssid)), 
                                        Uri: pb.Uint32(uint32(uri)), 
                                        Action: proto.Action(action).Enum(),
                                        Bin: []byte(sbin)}
    return py.IncNone(), nil
}

