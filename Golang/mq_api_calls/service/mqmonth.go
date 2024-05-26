package service

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"mq_api_calls/commons"
	"mq_api_calls/jwt"
	"net/http"
)

type MqMonthService struct {
	ClientID   string
	ResourceID string
	PrivateKey string
	PublicKey  string
	BaseURL    string
}

func NewMqMonthService() *MqMonthService {
	config := commons.GetMqMonthConfig()
	return &MqMonthService{
		ClientID:   config.ClientID,
		ResourceID: config.ResourceID,
		PrivateKey: config.PrivateKey,
		PublicKey:  config.PublicKey,
		BaseURL:    config.BaseURL,
	}
}

func (s *MqMonthService) GetQmgrs() {
	token, err := jwt.GenerateJWTToken(s.ClientID, s.ResourceID, s.PrivateKey, s.PublicKey)
	if err != nil {
		fmt.Printf("Error generating JWT token: %v\n", err)
		return
	}

	req, err := http.NewRequest("GET", s.BaseURL+"/get_qmgrs", nil)
	if err != nil {
		fmt.Printf("Error creating GET request: %v\n", err)
		return
	}
	req.Header.Set("Authorization", "Bearer "+token)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Error making GET request: %v\n", err)
		return
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error reading response body: %v\n", err)
		return
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		fmt.Printf("Error parsing JSON response: %v\n", err)
		return
	}

	fmt.Println("GET Response:", result)
}

func (s *MqMonthService) PostGmrs() {
	// Similar implementation for POST request
}

func (s *MqMonthService) DeleteWmgrs() {
	// Similar implementation for DELETE request
}
