package script

import (
	"fmt"
	"log"

	"github.com/qiniu/py"
)

type LogModule struct {
	logChan chan *LogItem
}

type LogItem struct {
	Level   string
	Content string
}

func NewLogModule() *LogModule {
	mod := &LogModule{logChan: make(chan *LogItem, 10240)}
	go mod.logging()
	return mod
}

func (this *LogModule) logging() {
	for item := range this.logChan {
		log.Println(item.Level, item.Content)
	}
}

func (this *LogModule) DoLog(level string, args *py.Tuple) {
	var content string
	err := py.Parse(args, &content)
	if err != nil {
		fmt.Println("Log err:", err)
		return
	}

	this.logChan <- &LogItem{Level: level, Content: content}
}

func (this *LogModule) Py_debug(args *py.Tuple) (ret *py.Base, err error) {
	this.DoLog("[DEBUG]", args)
	return py.IncNone(), nil
}

func (this *LogModule) Py_info(args *py.Tuple) (ret *py.Base, err error) {
	this.DoLog("[INFO]", args)
	return py.IncNone(), nil
}

func (this *LogModule) Py_warn(args *py.Tuple) (ret *py.Base, err error) {
	this.DoLog("[WARN]", args)
	return py.IncNone(), nil
}

func (this *LogModule) Py_error(args *py.Tuple) (ret *py.Base, err error) {
	this.DoLog("[ERROR]", args)
	return py.IncNone(), nil
}

func (this *LogModule) Py_fatal(args *py.Tuple) (ret *py.Base, err error) {
	this.DoLog("[FATAL]", args)
	return py.IncNone(), nil
}
