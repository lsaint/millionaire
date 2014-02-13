package network

import (
    "fmt"
    "net"
    "math/rand"
    "encoding/binary"

    pb "code.google.com/p/goprotobuf/proto"

    "millionaire/proto"
)

const (
    URI_REGISTER        = 1
    URI_TRANSPORT       = 2
    URI_UNREGISTER      = 3
    LEN_URI             = 2
    LEN_FID             = 2
    GATE_PORT          = ":40212"
)
 
type ConnBuff struct {
    conn    *ClientConnection
    buff    []byte
}

type Gate struct {
    buffChan            chan *ConnBuff
    fid2frontend        map[uint16]*ClientConnection         
    fids                []uint16
    GateInChan          chan *proto.GateInPack
    GateOutPack         chan *proto.GateOutPack
}

func NewGate(entry chan *proto.GateInPack,  exit chan *proto.GateOutPack) *Gate {
    gs := &Gate{buffChan: make(chan *ConnBuff),
                    fid2frontend:  make(map[uint16]*ClientConnection),
                    fids: make([]uint16, 0)
                    GateInChan: entry,
                    GateOutPack:  exit}
    go gs.parse()
    return gs
}


func (this *Gate) Start() {
    ln, err := net.Listen("tcp", GATE_PORT)                                                                            
    if err != nil {
        fmt.Println("Listen err", err)
        return
    }
    fmt.Println("Gate running", GATE_PORT)
    for {
        conn, err := ln.Accept()
        if err != nil {
            fmt.Println("Accept error", err)
            continue
        }
        fmt.Println("frontend connected")
        go this.acceptConn(conn)
    }
}

func (this *Gate) acceptConn(conn net.Conn) {
    cliConn := NewClientConnection(conn)
    for {
        if buff_body, ok := cliConn.duplexReadBody(); ok {
            this.buffChan <- &ConnBuff{cliConn, buff_body}
            continue
        }
        this.buffChan <- &ConnBuff{cliConn, nil}
        break
    }
    fmt.Println("frontend disconnect")
}

func (this *Gate) parse() {
    for { select {
        case conn_buff := <-this.buffChan :
            msg := conn_buff.buff
            conn := conn_buff.conn
            if msg == nil {
                this.unregister(conn)
                continue
            }

            f_uri := binary.LittleEndian.Uint16(msg[:LEN_URI])
            switch f_uri {
                case URI_REGISTER:
                    this.register(msg[LEN_URI:], conn)
                case URI_TRANSPORT:
                    this.comein(msg[LEN_URI:])
                case URI_UNREGISTER:
                    this.unregister(conn)
            }

        case pack := <-this.GateOutPack:
            this.comeout(pack)
    }}
}

func (this *Gate) unpack(b []byte) (msg *proto.GateInPack, err error) {
    fp := &proto.FrontendPack{}
    if err = pb.Unmarshal(b, fp); err != nil {
        fmt.Println("pb Unmarshal FrontendPack", err)
        lp = &proto.LogicPack{}
        if err = pb.Unmarshal(fp.Bin, lp); err != nil {
            fmt.Println("pb Unmarshal LogicPack", err)
            msg = &proto.GateInPack{tsid: fp.GetTsid(), ssid: fp.GetSsid(),
                                    uri: lp.GetUri(), bin: lp.Bin}
        }
    }
    return
}

func (this *Gate) comein(b []byte) {
    if msg, err := this.unpack(b); err == nil {
        this.GateInPack <- msg
    }
}

func (this *Gate) comeout(pack *proto.GateOutPack) {
    if l := len(this.fids); l == 0 {
        return
    }
    if pack.GetAction() == proto.Action_Broadcast {
        // broadcast
        for _, conn := range this.fid2frontend {
            conn.Send(this.doPack(pack))
        }
    } else {
        // randomcast
        cc := this.fid2frontend[this.fids[rand.Intn(l)]]
        cc.Send(this.doPack(pack))
    }
}

func (this *Gate) doPack(pack *proto.GateOutPack) b []byte {
    lp := &proto.LogicPack{uri: pack.GetUri(), bin: pack.Bin}
    if data, err := pb.Marshal(lp); err == nil {
        fp := &proto.FrontendPack{tsid: pack.GetTsid(), ssid: pack.GetSsid(), bin: data}
        if data, err = pb.Marshal(fp); err == nil {
            uri_field := make([]byte, LEN_URI)
            binary.LittleEndian.PutUint16(uri_field, uint16(URI_TRANSPORT))
            return append(uri_field, data...)
        }
    }
}

func (this *Gate) register(b []byte, cc *ClientConnection) {
    fid := binary.LittleEndian.Uint16(b[:LEN_FID])
    if fid == 0 {
        fmt.Println("fid 0 err")
        return
    }
    cc_ex := this.fid2frontend[fid]
    if !cc_ex {
        this.fid2frontend[fid] = cc
        this.fids = append(this.fids, fid)
    } else {
        this.unregister(cc_ex)
    }
    fmt.Println("register fid:", fid)
}

func (this *Gate) unregister(cc *ClientConnection) {
    fmt.Println("unregister")
    for fid, c := range this.fid2frontend {
        if c == cc {
            this.fid2frontend[fid] = nil
            for i, f := range this.fids {
                if fid == f {
                    last := len(this.fids) - 1
                    this.fids[i] = this.fids[last]
                    this.fids = this.fids[:last]
                }
            }
        }
    }
}

