FROM golang

COPY . /go/src/app
WORKDIR /go/src/app

RUN go get -d -v && go install

EXPOSE 3000

CMD app