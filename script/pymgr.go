package script

import (
    "fmt"
    "time"
    
    "github.com/qiniu/py"
    "millionaire/proto"
)

const (
    PROTO_INVOKE = iota
    UPDATE_INVOKE = iota
    NET_CTRL  = iota
    POST_DONE = iota
)


type PyMgr struct {
    recvChan         chan *proto.GateInPack
    sendChan         chan *proto.GateOutPack
    mod              *py.Module
}

func NewPyMgr(in chan *proto.GateInPack,  out chan *proto.GateOutPack) *PyMgr {
    mgr := &PyMgr{recvChan: in, sendChan: out}
    code, err := py.CompileFile("./becall.py", py.FileInput)
    if err != nil {
        fmt.Println(err)
        panic("Compile failed")
    }
    defer code.Decref()

    mgr.mod, err = py.ExecCodeModule("gopy", code.Obj())
    if err != nil {
        fmt.Println(err)
        panic("ExecCodeModule failed")
    }
    //defer mod.Decref()
    return  mgr
}

func (this *PyMgr) Start() {
}

func (this *PyMgr) loop() {
    ticker := time.Tick(1 * time.Second)
    for { select {
        case <-ticker:
            this.onTicker()
        case pack := <-this.recvChan:
            this.onProto(pack)
    }}
}

func (this *PyMgr) onProto(pack *proto.GateInPack) {
    tsid := py.NewInt64(int64(pack.GetTsid())); defer tsid.Decref()
    ssid := py.NewInt64(int64(pack.GetSsid())); defer ssid.Decref()
    uri := py.NewInt(int(pack.GetUri())); defer uri.Decref()
    data := py.NewString(string(pack.Bin)); defer data.Decref()
    _, err := this.mod.CallMethodObjArgs("OnProto", tsid.Obj(), ssid.Obj(), uri.Obj(), data.Obj())
    if err != nil {
        fmt.Println("OnProto err:", err)
        py.Raise(err)
    }
}

func (this *PyMgr) onTicker() {
}

