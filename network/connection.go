package network

import (
	"bufio"
	"encoding/binary"
	"log"
	"net"
	"time"
)

const (
	LEN_HEAD     = 4
	LEN_URI      = 4
	LEN_EXTRA    = LEN_HEAD // 总长度包括包长
	MAX_LEN_HEAD = 10240
)

type ClientConnection struct {
	conn     net.Conn
	reader   *bufio.Reader
	writer   *bufio.Writer
	sendchan chan []byte
}

func NewClientConnection(c net.Conn) *ClientConnection {
	cliConn := new(ClientConnection)
	cliConn.conn = c
	cliConn.reader = bufio.NewReader(c)
	cliConn.writer = bufio.NewWriter(c)
	cliConn.sendchan = make(chan []byte, BUF_COUNT)
	return cliConn
}

func (this *ClientConnection) Send(buf []byte) {
	head := make([]byte, LEN_HEAD)
	binary.LittleEndian.PutUint32(head, uint32(len(buf)+LEN_EXTRA))
	buf = append(head, buf...)

	select {
	case this.sendchan <- buf:

	default:
		log.Println("[Error]sendchan overflow or closed")
	}
}

func (this *ClientConnection) sendall() bool {
	for more := true; more; {
		select {
		case b := <-this.sendchan:
			if _, err := this.writer.Write(b); err != nil {
				log.Println("[Error]writer Write:", err)
				return false
			}
		default:
			more = false
		}
	}

	if err := this.writer.Flush(); err != nil {
		log.Println("[Error]writer Flush:", err)
		return false
	}
	return true
}

func (this *ClientConnection) duplexRead(buff []byte) bool {
	var read_size int
	for {
		// write
		if !this.sendall() {
			break
		}

		// read
		this.conn.SetReadDeadline(time.Now().Add(1e7))
		n, err := this.reader.Read(buff[read_size:])
		if err != nil {
			if e, ok := err.(*net.OpError); ok && e.Temporary() {
				read_size = n
				continue
			} else {
				//log.Println("read err disconnect:", err)
				break
			}
		}

		if n == 0 {
			return true
		}
		if n < len(buff) {
			read_size += n
			continue
		}
		return true
	}
	return false
}

func (this *ClientConnection) duplexReadBody() (ret []byte, ok bool) {
	buff_head := make([]byte, LEN_HEAD)
	if !this.duplexRead(buff_head) {
		return
	}
	len_head := binary.LittleEndian.Uint32(buff_head) - LEN_EXTRA
	if len_head > MAX_LEN_HEAD {
		log.Println("[Error]message len too long", len_head, string(buff_head))
		return
	}
	ret = make([]byte, len_head)
	if !this.duplexRead(ret) {
		return
	}
	ok = true
	return
}

func (this *ClientConnection) Close() {
	this.conn.Close()
	//close(this.sendchan)
}

type ConnBuff struct {
	conn *ClientConnection
	buff []byte
}
