package script

import (
    "log"
    "time"
    "encoding/base64"
    
    "github.com/qiniu/py"
    "millionaire/proto"
    "millionaire/postman"
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
    pm               *postman.Postman
    pymod            *py.Module 
    gomod            py.GoModule
}

func NewPyMgr(in chan *proto.GateInPack,  out chan *proto.GateOutPack) *PyMgr {
    mgr := &PyMgr{recvChan: in, sendChan: out, pm: postman.NewPostman()}
    var err error
    mgr.gomod, err = py.NewGoModule("go", "", NewGoModule(out, mgr.pm))
    // defer gomod.Decref()
    if err != nil {
        log.Fatalln("NewGoModule failed:", err)
    }

    code, err := py.CompileFile("./script/glue.py", py.FileInput)
    if err != nil {
        log.Fatalln("Compile failed:", err)
    }
    defer code.Decref()

    mgr.pymod, err = py.ExecCodeModule("glue", code.Obj())
    if err != nil {
        log.Fatalln("ExecCodeModule glue err:", err)
    }
    _, err = mgr.pymod.CallMethodObjArgs("test")
    // defer mgr.pymode.Decref()
    if err != nil {
        log.Fatalln("ExecCodeModule failed:", err)
    }
    return  mgr
}

func (this *PyMgr) Start() {
    ticker := time.Tick(1 * time.Second)
    for { select {
        case <-ticker:
            this.onTicker()
        case pack := <-this.recvChan:
            this.onProto(pack)
        case post_ret := <-this.pm.DoneChan:
            this.onPostDone(post_ret.Sn, <-post_ret.Ret)
    }}
}

func (this *PyMgr) onProto(pack *proto.GateInPack) {
    tsid := py.NewInt64(int64(pack.GetTsid())); defer tsid.Decref()
    ssid := py.NewInt64(int64(pack.GetSsid())); defer ssid.Decref()
    uri := py.NewInt(int(pack.GetUri())); defer uri.Decref()
    b := base64.StdEncoding.EncodeToString(pack.Bin)
    data := py.NewString(string(b)); defer data.Decref()
    _, err := this.pymod.CallMethodObjArgs("OnProto", tsid.Obj(), ssid.Obj(), uri.Obj(), data.Obj())
    if err != nil {
        log.Println("OnProto err:", err)
    }
}

func (this *PyMgr) onTicker() {
    if _, err := this.pymod.CallMethodObjArgs("OnTicker"); err != nil {
        log.Println("onTicker err:", err)
    }
}

func (this *PyMgr) onPostDone(sn int64, ret string) {
    py_sn := py.NewInt64(sn); defer py_sn.Decref()
    py_ret := py.NewString(string(ret)); defer py_ret.Decref()
    if _, err := this.pymod.CallMethodObjArgs("OnPostDone", py_sn.Obj(), py_ret.Obj()); err != nil {
        log.Println("onPostDone err:", err)
    }
}


