package script

import (
    //"fmt"
    
    "millionaire/proto"
)

var SN int64
const (
    PROTO_INVOKE = iota
    UPDATE_INVOKE = iota
    NET_CTRL  = iota
    POST_DONE = iota
)


type StateInPack struct {
    sid         float64
    uid         float64    
    pname       string
    data        string
}

type PyState struct {
    //state               *lua.State
    stateInChan         chan *StateInPack
    stateOutChan        chan *proto.GateOutPack
    //pm                  *postman.Postman             
    ctrlChan            chan string
}

////

type PyMgr struct {
}

func NewPyMgr() *PyMgr {
    return new(PyMgr)
}

func (this *PyMgr) Start(out chan *proto.GateOutPack, in chan *proto.GateInPack) {
}

func (this *PyMgr) loop() {
    ticker := time.Tick(1 * time.Second)
    for { select {
        case <-ticker:
            this.invokePython()
    }}
}

func (this *PyMgr) invokePython() {
}

