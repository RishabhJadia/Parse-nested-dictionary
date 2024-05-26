// commons/config.go

package commons

import (
	"encoding/json"
	"io/ioutil"
)

type Config struct {
	ClientID   string `json:"client_id"`
	ResourceID string `json:"resource_id"`
	PublicKey  string `json:"public_key"`
	PrivateKey string `json:"private_key"`
	BaseURL    string `json:"base_url"`
}

func GetMqMonthConfig() *Config {
	configData, err := ioutil.ReadFile("config.json")
	if err != nil {
		panic(err)
	}

	var config map[string]Config
	if err := json.Unmarshal(configData, &config); err != nil {
		panic(err)
	}

	return &config["MqMonth"]
}

func GetInvAdminConfig() *Config {
	configData, err := ioutil.ReadFile("config.json")
	if err != nil {
		panic(err)
	}

	var config map[string]Config
	if err := json.Unmarshal(configData, &config); err != nil {
		panic(err)
	}

	return &config["InvAdmin"]
}
