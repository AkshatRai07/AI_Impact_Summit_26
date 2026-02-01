FROM golang:1.25 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o job-portal .

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/job-portal .

EXPOSE 8080
CMD ["./job-portal"]
