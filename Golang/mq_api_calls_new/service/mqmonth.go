// https://chatgpt.com/c/76e01c4d-0bf1-47e3-a3bb-caf7bc5bdc2e#:~:text=Step%201%3A%20Create%20a%20Shared%20Package

package services

import (
	"bytes"
	"encoding/json"
	"fmt"
	"mq_api_calls_new/config"
	"mq_api_calls_new/jwt"
	"net/http"
)

// CallMqMonthAPI generates a JWT token for MqMonth service and returns the parsed response
func CallMqMonthAPI() (map[string]interface{}, error) {
	serviceConfig, err := config.LoadConfig("MqMonth")
	if err != nil {
		return nil, err
	}

	return jwt.GenerateJWTToken(serviceConfig.PrivateKey, serviceConfig.PublicKey, serviceConfig.ClientID, serviceConfig.ResourceID, serviceConfig.BaseURL)
}

// GetAccessToken extracts the access token from the API response
func GetAccessToken(response map[string]interface{}) (string, error) {
	if accessToken, ok := response["access_token"]; ok {
		return accessToken.(string), nil
	}
	return "", fmt.Errorf("access token not found in response")
}

// GetQmgrs fetches the Qmgrs data from the MqMonth service
func GetQmgrs() (map[string]interface{}, error) {
	response, err := CallMqMonthAPI()
	if err != nil {
		return nil, fmt.Errorf("failed to get token: %v", err)
	}

	accessToken, err := GetAccessToken(response)
	if err != nil {
		return nil, err
	}

	return makeRequest("GET", "/qmgrs", accessToken, nil)
}

// PostQmgrs sends data to the Qmgrs endpoint of the MqMonth service
func PostQmgrs(data map[string]interface{}) (map[string]interface{}, error) {
	response, err := CallMqMonthAPI()
	if err != nil {
		return nil, fmt.Errorf("failed to get token: %v", err)
	}

	accessToken, err := GetAccessToken(response)
	if err != nil {
		return nil, err
	}

	return makeRequest("POST", "/qmgrs", accessToken, data)
}

// DeleteQmgrs deletes data from the Qmgrs endpoint of the MqMonth service
func DeleteQmgrs(id string) (map[string]interface{}, error) {
	response, err := CallMqMonthAPI()
	if err != nil {
		return nil, fmt.Errorf("failed to get token: %v", err)
	}

	accessToken, err := GetAccessToken(response)
	if err != nil {
		return nil, err
	}

	return makeRequest("DELETE", "/qmgrs/"+id, accessToken, nil)
}

// makeRequest makes an HTTP request to the MqMonth service
func makeRequest(method, endpoint, accessToken string, data map[string]interface{}) (map[string]interface{}, error) {
	serviceConfig, err := config.LoadConfig("MqMonth")
	if err != nil {
		return nil, err
	}

	var reqBody []byte
	if data != nil {
		reqBody, err = json.Marshal(data)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %v", err)
		}
	}

	req, err := http.NewRequest(method, serviceConfig.BaseURL+endpoint, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}
	req.Header.Set("Authorization", "Bearer "+accessToken)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %v", err)
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	// similar to unmarshall.. convert json into Go data structure
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	return result, nil

	/*
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, err
		}

		var result map[string]interface{}
		err = json.Unmarshal(body, &result)
		if err != nil {
			return nil, err
		}

		return result, nil
	*/
}
