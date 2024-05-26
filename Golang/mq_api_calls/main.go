package main

import (
	"mq_api_calls/service"
)

func main() {
	// Initialize MqMonth service
	mqMonthService := service.NewMqMonthService()
	mqMonthService.GetQmgrs()
}
