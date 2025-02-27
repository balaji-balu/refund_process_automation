FROM golang:1.22
WORKDIR /app
COPY . .
RUN go mod tidy
RUN CGO_ENABLED=0 go build -o refund-api
CMD ["./refund-api"]
