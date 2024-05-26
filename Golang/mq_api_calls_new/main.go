package main

import (
	"fmt"
	"log"
	services "mq_api_calls_new/service"
)

func main() {
	// Example: Call GetQmgrs
	response, err := services.GetQmgrs()
	if err != nil {
		log.Fatalf("Failed to get Qmgrs: %v", err)
	}
	fmt.Printf("Response from GetQmgrs: %v\n", response)

	// Example: Call PostQmgrs
	postData := map[string]interface{}{
		"name": "NewQmgr",
		"data": "SomeData",
	}
	response, err = services.PostQmgrs(postData)
	if err != nil {
		log.Fatalf("Failed to post Qmgrs: %v", err)
	}
	fmt.Printf("Response from PostQmgrs: %v\n", response)

	// Example: Call DeleteQmgrs
	response, err = services.DeleteQmgrs("some-id")
	if err != nil {
		log.Fatalf("Failed to delete Qmgrs: %v", err)
	}
	fmt.Printf("Response from DeleteQmgrs: %v\n", response)
}
