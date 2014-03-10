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
    GATE_PORT          = ":40214"
)
 
type Gate struct {
    buffChan            chan *ConnBuff
    fid2frontend        map[uint32]*ClientConnection         
    uid2fid             map[uint32]uint32
    fids                []uint32
    GateInChan          chan *proto.GateInPack
    GateOutChan         chan *proto.GateOutPack
}

func NewGate(entry chan *proto.GateInPack,  exit chan *proto.GateOutPack) *Gate {
    gs := &Gate{buffChan: make(chan *ConnBuff),
                    fid2frontend:  make(map[uint32]*ClientConnection),
                    uid2fid: make(map[uint32]uint32),
                    fids: make([]uint32, 0),
                    GateInChan: entry,
                    GateOutChan:  exit}
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
            //fmt.Println("len=", len(msg), "msg=", string(msg), "byte=", msg)
            len_msg := len(msg)
            if len_msg < LEN_URI {
                continue
            } 

            f_uri := binary.LittleEndian.Uint32(msg[:LEN_URI])
            //fmt.Println("f_uri=", f_uri)
            switch f_uri {
                case URI_REGISTER:
                    this.register(msg[LEN_URI:], conn)
                case URI_TRANSPORT:
                    this.comein(msg[LEN_URI:])
                case URI_UNREGISTER:
                    this.unregister(conn)
            }

        case pack := <-this.GateOutChan:
            this.comeout(pack)
    }}
}

func (this *Gate) unpack(b []byte) (msg *proto.GateInPack, err error) {
    fp := &proto.FrontendPack{}
    if err = pb.Unmarshal(b, fp); err == nil {
        // register uid2fid
        if fp.GetUid() != 0 {
            this.uid2fid[fp.GetUid()] = fp.GetFid()
        }
        msg = &proto.GateInPack{Tsid: fp.Tsid, Ssid: fp.Ssid, Uri: fp.Uri, Bin: fp.Bin}
    } else {
        fmt.Println("pb Unmarshal FrontendPack", err)
    }
    return
}

func (this *Gate) comein(b []byte) {
    if msg, err := this.unpack(b); err == nil {
        this.GateInChan <- msg
    }
}

func (this *Gate) randomFid() uint32 {
    return this.fids[rand.Intn(len(this.fids))]
}

func (this *Gate) comeout(pack *proto.GateOutPack) {
    //fmt.Println("coming out", pack, "fid2frontend", this.fid2frontend)
    l := len(this.fids)
    if l == 0 { return }
    p, rfid := this.doPack(pack)

    switch pack.GetAction() {
        case proto.Action_Broadcast:
            for _, conn := range this.fid2frontend {
                conn.Send(p)
                //fmt.Println("broadcast", len(p))
            }
        case proto.Action_Randomcast:
            if cc := this.fid2frontend[rfid]; cc != nil {
                cc.Send(p)
                //fmt.Println("randomcast", len(p))
            } else {
                fmt.Println("random not find fid2frontend", rfid)
            }
        case proto.Action_Specify:
            if fid := this.uid2fid[pack.GetUid()]; fid != 0 {
                if cc := this.fid2frontend[fid]; cc != nil {
                    cc.Send(p)
                    //fmt.Println("specify", len(p))
                } else {
                    fmt.Println("not find fid2frontend", fid)
                }
            } else {
                fmt.Println("not find uid2fid", pack.GetUid())
            }
    }
}

func (this *Gate) doPack(pack *proto.GateOutPack) (ret []byte, fid uint32) {
    fp := &proto.FrontendPack{Uri: pack.Uri, Tsid: pack.Tsid, Ssid: pack.Ssid, Bin: pack.Bin}
    switch pack.GetAction() {
        case proto.Action_Broadcast:
            fp.Fid = pb.Uint32(this.randomFid())
        case proto.Action_Randomcast:
            fid = this.randomFid()
            fp.Fid = pb.Uint32(fid)
        case proto.Action_Specify:
            fp.Uid = pack.Uid
    }
    if data, err := pb.Marshal(fp); err == nil {
        uri_field := make([]byte, LEN_URI)
        binary.LittleEndian.PutUint32(uri_field, uint32(URI_TRANSPORT))
        ret = append(uri_field, data...)
    } else {
        fmt.Println("pack FrontendPack err", err)
    }
    return
}

func (this *Gate) register(b []byte, cc *ClientConnection) {
    fp := &proto.FrontendRegister{}
    //fmt.Println("unpacking ->", len(b), b, string(b))
    if err := pb.Unmarshal(b, fp); err == nil {
        fid := uint32(fp.GetFid())
        if fid == 0 {
            fmt.Println("fid 0 err")
            return
        }
        cc_ex, exist := this.fid2frontend[fid]
        if exist {
            this.unregister(cc_ex)
        }
        this.fid2frontend[fid] = cc
        this.fids = append(this.fids, fid)
        fmt.Println("register fid:", fid)
    } else {
        fmt.Println("Unmarshal register pack err")
    }
}

func (this *Gate) unregister(cc *ClientConnection) {
    for fid, c := range this.fid2frontend {
        if c == cc {
            //this.fid2frontend[fid] = nil
            delete(this.fid2frontend, fid)
            fmt.Println("unregister", fid)
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

