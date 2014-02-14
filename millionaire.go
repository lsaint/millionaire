// L'millionaire

package main

import (
    "fmt"
    "os"
    "syscall"
    "os/signal"
    "runtime"
    //"net/http"
    //"log"
    //_ "net/http/pprof"

    "millionaire/script"
    "millionaire/network"
    "millionaire/proto"
    //"millionaire/conf"
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

    in := make(chan *proto.GateInPack, 10240)
    out := make(chan *proto.GateOutPack, 10240)
    pymgr := script.NewPyMgr(in, out)
    gate := network.NewGate(in, out)
    go gate.Start()
    go pymgr.Start()

    handleSig()
}

