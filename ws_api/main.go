package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"

	jwt "github.com/dgrijalva/jwt-go"
	"github.com/gorilla/websocket"
	uuid "github.com/satori/go.uuid"
	"github.com/streadway/amqp"
)

// ConfigFilePath path to json config file
const ConfigFilePath = "config.json"

// Config application config
type Config struct {
	WorkersCount   int
	ExchangeName   string
	Port           string
	Debug          bool
	RabbitURL      string
	AuthSecretKey  string
	AuthCookieName string
}

func readConfig() (*Config, error) {
	data, err := ioutil.ReadFile(ConfigFilePath)
	if err != nil {
		return nil, err
	}
	config := new(Config)
	err = json.Unmarshal(data, config)
	if err != nil {
		return nil, err
	}
	return config, nil
}

func createUUID() string {
	return uuid.Must(uuid.NewV4()).String()
}

func failOnError(err error, msg string) {
	if err != nil {
		fmt.Printf("%s: %s", msg, err)
		panic(fmt.Sprintf("%s: %s", msg, err))
	}
}

// Connections websocket connections slice
type Connections []*websocket.Conn

// RemoveNIL remove nil pointers from connections
func (conns Connections) RemoveNIL() Connections {
	current := 0
	for i := range conns {
		if conns[i] != nil {
			if current != i {
				conns[current] = conns[i]
			}
			current++
		}
	}
	return conns[:current]
}

func (conns Connections) CloseAll() {
	// Close all connections
}

// Group connections group
type Group struct {
	Connections Connections
	Lock        sync.Mutex
}

func (g *Group) CloseAll() {
	// Close all connections
}

// Queue class
type Queue struct {
	url          string
	exchangeName string
	queueName    string
	conn         *amqp.Connection
	channel      *amqp.Channel
	queue        *amqp.Queue
}

// NewQueue creates new Queue instance
func NewQueue(url, exchangeName, queueName string) (*Queue, error) {
	queue := Queue{
		url:          url,
		exchangeName: exchangeName,
		queueName:    queueName,
	}
	err := queue.Connect()
	if err != nil {
		return nil, err
	}
	err = queue.Declare()
	if err != nil {
		return nil, err
	}

	return &queue, nil
}

// Connect create connection and channel
func (q *Queue) Connect() error {
	conn, err := amqp.Dial(q.url)
	if err != nil {
		return err
	}

	ch, err := conn.Channel()
	if err != nil {
		return err
	}

	q.conn = conn
	q.channel = ch
	return nil
}

// Close channel and dial connection
func (q *Queue) Close() {
	defer q.conn.Close()
	defer q.channel.Close()
}

// Declare creates exchange and queue for worker
func (q *Queue) Declare() error {
	err := q.channel.ExchangeDeclare(
		q.exchangeName,
		"headers",
		false,
		true,
		false,
		false,
		nil,
	)
	if err != nil {
		return err
	}

	queue, err := q.channel.QueueDeclare(
		q.queueName, // name
		true,        // durable
		true,        // delete when unused
		false,       // exclusive
		false,       // no-wait
		nil,         // arguments
	)
	if err != nil {
		return err
	}
	q.queue = &queue
	return nil
}

func (q *Queue) getBindTable(UserID int) amqp.Table {
	return amqp.Table{
		"UserID:" + strconv.Itoa(UserID): true,
		"x-match":                        "any",
	}
}

// Bind binds exchange and queue for accept user's messages
func (q *Queue) Bind(UserID int) error {
	err := q.channel.QueueBind(
		q.queue.Name,
		"",
		q.exchangeName,
		true,
		q.getBindTable(UserID),
	)
	if err != nil {
		return err
	}
	return nil
}

// Unbind unbinds exchange and queue
func (q *Queue) Unbind(UserID int) error {
	err := q.channel.QueueUnbind(
		q.queue.Name,
		"",
		q.exchangeName,
		q.getBindTable(UserID),
	)
	if err != nil {
		return err
	}
	return nil
}

// Consume starts messages consuming
func (q *Queue) Consume() (<-chan amqp.Delivery, error) {
	err := q.channel.Qos(
		10,    // prefetch count
		0,     // prefetch size
		false, // global
	)
	if err != nil {
		return nil, err
	}

	msgs, err := q.channel.Consume(
		q.queue.Name, // queue
		"",           // consumer
		false,        // auto-ack
		false,        // exclusive
		false,        // no-local
		false,        // no-wait
		nil,          // args
	)
	if err != nil {
		return nil, err
	}
	return msgs, nil
}

type workerMessage struct {
	UserIDs []int
	Message *amqp.Delivery
}

// Worker it works
type Worker struct {
	id        string
	groups    map[int]*Group
	lock      sync.Mutex
	config    *Config
	Queue     *Queue
	jobs      chan *workerMessage
	waitGroup sync.WaitGroup
}

// NewWorker create new worker
func NewWorker(config *Config) (*Worker, error) {
	id := createUUID()
	queue, err := NewQueue(config.RabbitURL, config.ExchangeName, id)
	if err != nil {
		return nil, err
	}
	return &Worker{
		groups: make(map[int]*Group),
		id:     id,
		config: config,
		Queue:  queue,
		jobs:   make(chan *workerMessage),
	}, nil
}

func (w *Worker) Close() {
	w.Queue.Close()
	close(w.jobs)
	w.waitGroup.Wait()
	// TODO Close connections
}

// Broadcast send message to all connections in group
func (w *Worker) Broadcast(groupIDs []int, message []byte) {
	w.lock.Lock()
	defer w.lock.Unlock()
	for _, groupID := range groupIDs {
		group, prs := w.groups[groupID]
		if !prs {
			return
		}
		group.Lock.Lock()
		defer group.Lock.Unlock()
		for i, conn := range group.Connections {
			if conn == nil {
				continue
			}
			err := conn.WriteMessage(websocket.TextMessage, message)
			if err != nil {
				fmt.Println(err)
				group.Connections[i] = nil
				defer conn.Close()
			}
		}
		group.Connections = group.Connections.RemoveNIL()
	}
}

func parseUserIDs(value string) (result []int, err error) {
	for _, userID := range strings.Split(value, ",") {
		id, err := strconv.Atoi(userID)
		if err != nil {
			return nil, err
		}
		result = append(result, id)
	}
	return result, nil
}

// Work just do your work
func (w *Worker) startMainWorker() {
	defer w.waitGroup.Done()
	messages, err := w.Queue.Consume()
	failOnError(err, "Fail to start consumer")
	for msg := range messages {
		fmt.Println(msg)
		value, prs := msg.Headers["UserIDs"]
		if !prs {
			fmt.Println("Error group name has not type string")
			msg.Reject(false)
			continue
		}

		UserIDs, err := parseUserIDs(value.(string))
		if err != nil {
			fmt.Println("Error group name has not type string")
			msg.Reject(false)
			continue
		}

		w.jobs <- &workerMessage{UserIDs, &msg}
	}
}

func (w *Worker) startSecondaryWorker() {
	defer w.waitGroup.Done()
	for msg := range w.jobs {
		w.Broadcast(msg.UserIDs, msg.Message.Body)
		msg.Message.Ack(false)
	}
}

// Start Create main worker and few secondary workers
func (w *Worker) Start() {
	for i := 1; i < w.config.WorkersCount; i++ {
		w.waitGroup.Add(1)
		go w.startSecondaryWorker()
	}
	w.waitGroup.Add(1)
	go w.startMainWorker()
}

// AddConn add connection
func (w *Worker) AddConn(UserID int, conn *websocket.Conn) {
	defer w.lock.Unlock()
	w.lock.Lock()
	err := w.Queue.Bind(UserID)
	if err != nil {
		fmt.Println(err)
		return
	}
	group, prs := w.groups[UserID]
	if !prs {
		group = &Group{Connections: make(Connections, 0)}
		w.groups[UserID] = group
	}
	group.Lock.Lock()
	defer group.Lock.Unlock()
	group.Connections = append(group.Connections, conn)
}

var (
	upgrader = websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin: func(r *http.Request) bool {
			// allow all connections
			return true
		},
	}
	jwtParser = jwt.Parser{}
)

func validateToken(token, secret string) (*jwt.Token, error) {
	return jwtParser.Parse(
		token,
		func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("Unexpected signing method: %v", token.Header["alg"])
			}
			return []byte(secret), nil
		},
	)
}

func main() {
	config, err := readConfig()
	failOnError(err, "Fail to read config")

	worker, err := NewWorker(config)
	failOnError(err, "Fail to create worker")
	worker.Start()
	defer worker.Close()

	http.HandleFunc("/wsapi/stream", func(w http.ResponseWriter, r *http.Request) {
		authCookie, err := r.Cookie(config.AuthCookieName)
		if err != nil {
			fmt.Println("No cookie")
			fmt.Println(err)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		token, err := validateToken(authCookie.Value, config.AuthSecretKey)
		if err != nil || !token.Valid {
			fmt.Println("Invalid token")
			fmt.Println(err)
			fmt.Println([]byte(config.AuthSecretKey))
			fmt.Println(token)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			fmt.Println("Error claims parsing")
			fmt.Println(token.Claims)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}

		fmt.Println(claims)

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			fmt.Println(err)
			return
		}

		userID, _ := strconv.Atoi(claims["id"].(string))
		worker.AddConn(userID, conn)
		fmt.Println("Client subscribed")
	})
	if config.Debug {
		indexFile, err := os.Open("index.html")
		failOnError(err, "Fail to open file")
		index, err := ioutil.ReadAll(indexFile)
		failOnError(err, "Fail")
		http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprintf(w, string(index))
		})
	}
	http.ListenAndServe(":"+config.Port, nil)
}

// TODO unbind
