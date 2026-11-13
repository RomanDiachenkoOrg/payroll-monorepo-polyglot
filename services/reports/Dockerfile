FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/reports .

FROM alpine:3.20
RUN adduser -D -H reports
USER reports
COPY --from=build /out/reports /usr/local/bin/reports
EXPOSE 8081
ENTRYPOINT ["/usr/local/bin/reports"]
