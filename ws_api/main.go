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
	"github.com/satori/go.uuid"
	"github.com/streadway/amqp"
)

// ConfigFilePath path to json config file
const ConfigFilePath = "config.json"

// Config application config
type Config struct {
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

// Group connections group
type Group struct {
	Connections Connections
	Lock        sync.Mutex
}

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

// Bind binds exchange and queue for accept user's messages
func (q *Queue) Bind(UserID int) error {
	err := q.channel.QueueBind(
		q.queue.Name,
		"",
		q.exchangeName,
		true,
		amqp.Table{
			"UserID:" + strconv.Itoa(UserID): true,
			"x-match":                        "any",
		},
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

// Worker it works
type Worker struct {
	id     string
	groups map[int]Group
	lock   sync.Mutex
	config *Config
	Queue  *Queue
}

// NewWorker create new worker
func NewWorker(config *Config) (*Worker, error) {
	id := createUUID()
	queue, err := NewQueue(config.RabbitURL, config.ExchangeName, id)
	if err != nil {
		return nil, err
	}
	return &Worker{
		groups: make(map[int]Group),
		id:     id,
		config: config,
		Queue:  queue,
	}, nil
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
		// TODO refactor use chan and Group worker
		go func() {
			group.Lock.Lock()
			defer group.Lock.Unlock()
			for i, conn := range group.Connections {
				if conn == nil {
					continue
				}
				err := conn.WriteMessage(websocket.TextMessage, message)
				if err != nil {
					group.Connections[i] = nil
					defer conn.Close()
				}
			}
			group.Connections = group.Connections.RemoveNIL()
		}()
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
func (w *Worker) Work() {
	messages, err := w.Queue.Consume()
	failOnError(err, "Fail to start consumer")
	for msg := range messages {
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

		go func(UserIDs []int, msg amqp.Delivery) {
			w.Broadcast(UserIDs, msg.Body)
			msg.Ack(false)
		}(UserIDs, msg)
	}
}

// AddConn add connection
func (w *Worker) AddConn(UserID int, conn *websocket.Conn) {
	defer w.lock.Unlock()
	w.lock.Lock()
	group, prs := w.groups[UserID]
	if prs {
		group.Lock.Lock()
		defer group.Lock.Unlock()
		group.Connections = append(group.Connections, conn)
	} else {
		group.Connections = append(make(Connections, 0), conn)
	}
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

// AuthTokenClaims extended token claims
type AuthTokenClaims struct {
	UserID int `json:"id"`
	jwt.StandardClaims
}

func validateToken(token, secret string) (*jwt.Token, error) {
	return jwtParser.Parse(
		token,
		func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("Unexpected signing method: %v", token.Header["alg"])
			}
			return secret, nil
		},
	)
}

func main() {
	config, err := readConfig()
	failOnError(err, "Fail to read config")

	worker, err := NewWorker(config)
	failOnError(err, "Fail to create worker")
	go worker.Work()

	http.HandleFunc("/wsapi/stream", func(w http.ResponseWriter, r *http.Request) {
		authCookie, err := r.Cookie(config.AuthCookieName)
		if err != nil {
			fmt.Println(err)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		token, err := validateToken(authCookie.Value, config.AuthSecretKey)
		if err != nil || !token.Valid {
			fmt.Println(err)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}

		claims, ok := token.Claims.(*AuthTokenClaims)
		if !ok {
			fmt.Println(err)
			w.WriteHeader(http.StatusUnauthorized)
			return
		}

		fmt.Println(claims.UserID)

		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			fmt.Println(err)
			return
		}
		fmt.Println("Client subscribed")

		worker.AddConn(claims.UserID, conn)
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

// TODO safe exit
// TODO unbind
