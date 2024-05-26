https://www.youtube.com/watch?v=a1SneuI65O0
https://golang.cafe/blog/golang-debugging-with-delve.html
go install github.com/go-delve/delve/cmd/dlv@latest
dlv debug main.go
breakpoint main.go:10
breakpoint main.go:11
breakpoint main.go:11
breakpoint
list main.go:10

For auto generate swagger doc
go install github.com/swaggo/swag/cmd/swag@latest
go get -u github.com/swaggo/gin-swagger
go get -u github.com/swaggo/files
swag init