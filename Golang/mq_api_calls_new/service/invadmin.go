package services

import (
	"mq_api_calls_new/config"
	"mq_api_calls_new/jwt"
)

// CallInvAdminAPI generates a JWT token for MqMonth service and returns the parsed response

func CallInvAdminAPI() (map[string]interface{}, error) {
	serviceConfig, err := config.LoadConfig("InvAdmin")
	if err != nil {
		return nil, err
	}

	return jwt.GenerateJWTToken(serviceConfig.PrivateKey, serviceConfig.PublicKey, serviceConfig.ClientID, serviceConfig.ResourceID, serviceConfig.BaseURL)
}
