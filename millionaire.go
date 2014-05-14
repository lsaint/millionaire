// L'millionaire

package main

import (
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"syscall"

	"millionaire/network"
	"millionaire/proto"
	"millionaire/script"
)

func handleSig() {
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)

	for sig := range c {
		fmt.Println("__handle__signal__", sig)
		return
	}
}

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	//go func() {
	//    log.Println(http.ListenAndServe("localhost:6061", nil))
	//}()

	BUF_COUNT := 102400
	in := make(chan *proto.GateInPack, BUF_COUNT)
	out := make(chan *proto.GateOutPack, BUF_COUNT)
	pymgr := script.NewPyMgr(in, out)
	gate := network.NewGate(in, out)
	go gate.Start()
	go pymgr.Start()

	handleSig()
}
