package main

import (
	"sync"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"time"

    "github.com/gorilla/websocket"
    "github.com/streadway/amqp"
	"github.com/satori/go.uuid"
)

func createUUID() string {
	return uuid.Must(uuid.NewV4()).String()
}

// Group connections group
type Group []*websocket.Conn

// Worker it works
type Worker struct {
    id string
    groups map[string]Group
    lock sync.Mutex
}

// NewWorker create new worker
func NewWorker() *Worker {
    return &Worker{groups:make(map[string]Group), id:createUUID()}
}

// Broadcast send message to all connections in group
func (w *Worker) Broadcast(groupName string, message []byte) {
    defer w.lock.Unlock()
    w.lock.Lock()
    group, prs := w.groups[groupName]
    if !prs {
        return
    }
    for _, conn := range group {
        // TODO check conn
        err := conn.WriteMessage(websocket.TextMessage, message)
        if err != nil {
            w.DelConn(groupName, conn)
        }
    }
}

func failOnError(err error, msg string) {
    if err != nil {
            fmt.Printf("%s: %s", msg, err)
            panic(fmt.Sprintf("%s: %s", msg, err))
    }
}

func (w *Worker) declareAndConnect() (<-chan amqp.Delivery){
    conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
    failOnError(err, "Failed to connect to RabbitMQ")
    defer conn.Close()

    ch, err := conn.Channel()
    failOnError(err, "Failed to open a channel")
    defer ch.Close()

    q, err := ch.QueueDeclare(
            "task_queue", // name
            true,         // durable
            true,        // delete when unused
            false,        // exclusive
            false,        // no-wait
            nil,          // arguments
    )
    failOnError(err, "Failed to declare a queue")

    err = ch.Qos(
            1,     // prefetch count
            0,     // prefetch size
            false, // global
    )
    failOnError(err, "Failed to set QoS")

    msgs, err := ch.Consume(
            q.Name, // queue
            "",     // consumer
            false,  // auto-ack
            false,  // exclusive
            false,  // no-local
            false,  // no-wait
            nil,    // args
    )
    failOnError(err, "Failed to register a consumer")
    return msgs
}

// Work just do your work
func (w *Worker) Work() {
    for {
        time.Sleep(2 * time.Second)
        
        for name := range w.groups {
            w.Broadcast(name, []byte("test test test"))
        }
    }
}

// AddConn add connection
func (w *Worker) AddConn(groupName string, conn *websocket.Conn) {
    // TODO too mutch locks
    defer w.lock.Unlock()
    w.lock.Lock()
    group, prs := w.groups[groupName]
    if prs {
        w.groups[groupName] = append(group, conn)
    } else {
        w.groups[groupName] = append(make(Group, 0), conn)
    }
}

// DelConn delete connection
func (w *Worker) DelConn(groupName string, conn *websocket.Conn) {
    defer w.lock.Unlock()
    w.lock.Lock()
    group, prs := w.groups[groupName]
    if !prs {
        return
    }
    i := 0
    for ; i < len(group); i++ {
        if group[i] == conn {
            break
        }
    }
    if i == len(group) {
        return
    }
    copy(group[i:], group[i+1:])
    group[len(group)-1] = nil
    group = group[:len(group)-1]
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func main() {
	indexFile, err := os.Open("ws_api/index.html")
	if err != nil {
		fmt.Println(err)
	}
	index, err := ioutil.ReadAll(indexFile)
	if err != nil {
		fmt.Println(err)
	}
    worker := NewWorker()
    go worker.Work()
	http.HandleFunc("/websocket", func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			fmt.Println(err)
			return
        }
        // defer conn.Close()

        fmt.Println("Client subscribed")
        name := r.URL.Query().Get("id")
        fmt.Println(name)
		worker.AddConn(name, conn)
	})
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, string(index))
    })
	http.ListenAndServe(":3000", nil)
}
// TODO safe exit
