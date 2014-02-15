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
    pymod            *py.Module 
    gomod            py.GoModule
}

func NewPyMgr(in chan *proto.GateInPack,  out chan *proto.GateOutPack) *PyMgr {
    mgr := &PyMgr{recvChan: in, sendChan: out}
    var err error
    mgr.gomod, err = py.NewGoModule("go", "", NewGoModule(out))
    // defer gomod.Decref()
    if err != nil {
        fmt.Println(err)
        panic("NewGoModule failed:")
    }

    code, err := py.CompileFile("./script/glue.py", py.FileInput)
    if err != nil {
        fmt.Println(err)
        panic("Compile failed")
    }
    defer code.Decref()

    mgr.pymod, err = py.ExecCodeModule("glue", code.Obj())
    _, err = mgr.pymod.CallMethodObjArgs("test")
    // defer mgr.pymode.Decref()
    if err != nil {
        fmt.Println(err)
        panic("ExecCodeModule failed")
    }
    return  mgr
}

func (this *PyMgr) Start() {
    ticker := time.Tick(1 * time.Second)
    for { select {
        case <-ticker:
            this.OnTicker()
        case pack := <-this.recvChan:
            this.onProto(pack)
    }}
}

func (this *PyMgr) onProto(pack *proto.GateInPack) {
    tsid := py.NewInt64(int64(pack.GetTsid())); defer tsid.Decref()
    ssid := py.NewInt64(int64(pack.GetSsid())); defer ssid.Decref()
    uri := py.NewInt(int(pack.GetUri())); defer uri.Decref()
    data := py.NewString(string(pack.Bin)); defer data.Decref()
    _, err := this.pymod.CallMethodObjArgs("OnProto", tsid.Obj(), ssid.Obj(), uri.Obj(), data.Obj())
    if err != nil {
        fmt.Println("OnProto err:", err)
    }
}

func (this *PyMgr) OnTicker() {
    if _, err := this.pymod.CallMethodObjArgs("OnTicker"); err != nil {
        fmt.Println("OnTicker err:", err)
    }
}

