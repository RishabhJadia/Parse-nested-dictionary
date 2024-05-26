package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type ServiceConfig struct {
	ClientID   string `json:"client_id"`
	ResourceID string `json:"resource_id"`
	PublicKey  string `json:"public_key"`
	PrivateKey string `json:"private_key"`
	BaseURL    string `json:"base_url"`
}

type ServicesConfig struct {
	Services map[string]ServiceConfig `json:"services"`
}

func LoadConfig(serviceName string) (*ServiceConfig, error) {
	/*
		configPath := filepath.Join("config", "config.json")
		configFile, err := os.Open(configPath)
		if err != nil {
			return nil, fmt.Errorf("failed to open config file: %v", err)
		}
		defer configFile.Close()

		var config map[string]map[string]ServiceConfig
		if err := json.NewDecoder(configFile).Decode(&config); err != nil {
			return nil, fmt.Errorf("failed to decode config file: %v", err)
		}

		serviceConfig, exists := config[serviceName]
		if !exists {
			return nil, fmt.Errorf("service %s not found in config file", serviceName)
		}

		return &serviceConfig, nil
	*/

	configPath := filepath.Join("config", "config.json")

	// Read entire file content
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %v", err)
	}
	// Define a struct to represent the entire config with services
	var config ServicesConfig
	// Unmarshal JSON into the Go struct
	err = json.Unmarshal(data, &config)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %v", err)
	}

	// Access the specific service configuration
	serviceConfig, exists := config.Services[serviceName]
	if !exists {
		return nil, fmt.Errorf("service %s not found in config file", serviceName)
	}

	return &serviceConfig, nil

}
