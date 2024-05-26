package service

import (
	"fmt"
	"mq_api_calls/commons"
	"mq_api_calls/jwt"
)

type InvAdminService struct {
	ClientID   string
	ResourceID string
	PrivateKey string
	BaseURL    string
}

func NewInvAdminService() *InvAdminService {
	config := commons.GetInvAdminConfig()
	return &InvAdminService{
		ClientID:   config.ClientID,
		ResourceID: config.ResourceID,
		PrivateKey: config.PrivateKey,
		BaseURL:    config.BaseURL,
	}
}

func (s *InvAdminService) DoSomething() {
	token, err := jwt.GenerateJWTToken(s.ClientID, s.ResourceID, s.PrivateKey)
	if err != nil {
		fmt.Printf("Error generating JWT token: %v\n", err)
		return
	}
	fmt.Printf("InvAdmin Token: %v\n", token)

	// Use token to call API
	// e.g., sendTokenRequest(s.BaseURL, token)
}
