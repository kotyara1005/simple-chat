FROM golang

COPY . /go/src/app
WORKDIR /go/src/app

RUN go get -d -v && go install

EXPOSE 3000

CMD ["./wait-for-it.sh", "rabbit:5672", "-s", "-t", "30", "--", "app"]