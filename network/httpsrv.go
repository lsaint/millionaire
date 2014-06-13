package network

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

const (
	MAX_REQ_COUNT = 1024
	TIME_OUT      = 30

	ENUM_ADD_MONEY = 1
	ENUM_LIST_ALL  = 2
)

type HttpReq struct {
	Req  string
	Ret  chan string
	Kind int
}

type HttpServer struct {
	reqChan chan *HttpReq
}

func NewHttpServer(c chan *HttpReq) *HttpServer {
	return &HttpServer{c}
}

func (this *HttpServer) Start() {
	http.HandleFunc("/millionaire/treasure/listall", func(w http.ResponseWriter, r *http.Request) {
		this.onReq(w, r, ENUM_LIST_ALL)
	})
	http.HandleFunc("/millionaire/addmoney", func(w http.ResponseWriter, r *http.Request) {
		this.onReq(w, r, ENUM_ADD_MONEY)
	})

	log.Println("http server running")
	http.ListenAndServe(":40613", nil)
}

func (this *HttpServer) onReq(w http.ResponseWriter, r *http.Request, kind int) {
	recv_post, err := ioutil.ReadAll(r.Body)
	if err != nil {
		fmt.Fprint(w, "")
		return
	}
	ret, ret_chan := "", make(chan string)
	select {
	case this.reqChan <- &HttpReq{string(recv_post), ret_chan, kind}:
		ret = <-ret_chan

	case <-time.After(TIME_OUT * time.Second):
	}

	fmt.Fprint(w, ret)
}
