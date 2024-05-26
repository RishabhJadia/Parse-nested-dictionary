package jwt

import (
	"crypto/rsa"
	"crypto/sha1"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/dgrijalva/jwt-go"
)

// validateAndJoinPath constructs the full path for a file within the "pki" directory and checks for errors.
func validateAndJoinPath(fileName string) (string, error) {
	if fileName == "" {
		return "", errors.New("file name cannot be empty")
	}
	fullPath := filepath.Join("pki", fileName)
	if _, err := os.Stat(fullPath); err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return "", fmt.Errorf("file not found: %s", fullPath)
		}
		// Handle other potential errors
		return "", err
	}
	return fullPath, nil
}

// LoadPrivateKey loads an RSA private key from the given path
func LoadPrivateKey(privateKeyPath string) (*rsa.PrivateKey, error) {
	privateKeyPath, err := validateAndJoinPath(privateKeyPath)
	if err != nil {
		return nil, err
	}
	priv, err := os.ReadFile(privateKeyPath)
	if err != nil {
		return nil, err
	}
	return jwt.ParseRSAPrivateKeyFromPEM(priv)
}

// getSha1Fingerprint calculates the SHA1 fingerprint of the given public key file
func getSha1Fingerprint(publicKeyPath string) (string, error) {
	publicKeyPath, err := validateAndJoinPath(publicKeyPath)
	if err != nil {
		return "", err
	}
	pemContent, err := os.ReadFile(publicKeyPath)
	if err != nil {
		return "", err
	}
	block, _ := pem.Decode(pemContent)
	if block == nil {
		return "", fmt.Errorf("failed to parse PEM file")
	}
	cert, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		return "", err
	}
	fingerprint := sha1.Sum(cert.Raw)
	var buf strings.Builder
	for i, f := range fingerprint {
		if i > 0 {
			fmt.Fprintf(&buf, ":")
		}
		fmt.Fprintf(&buf, "%02x", f)
	}
	return strings.ReplaceAll(buf.String(), ":", ""), nil
}

// parseAndPrintAccessToken parses the response body and prints the access token, returning the entire parsed response
func parseAndPrintAccessToken(body []byte) (map[string]interface{}, error) {
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		fmt.Printf("Error parsing response body: %v\n", err)
		return nil, err
	}
	if accessToken, ok := result["access_token"]; ok {
		fmt.Printf("Access Token: %v\n", accessToken)
	}
	return result, nil
}

// sendTokenRequest sends the JWT token to the server and returns the parsed response body
func sendTokenRequest(token, clientID, resourceID, baseURL string) (map[string]interface{}, error) {
	data := url.Values{}
	data.Set("grant_type", "client")
	data.Set("clnt_id", clientID)
	data.Set("resource", resourceID)
	data.Set("client_assertion", strings.TrimSpace(token))

	req, err := http.NewRequest("POST", baseURL+"/token", strings.NewReader(data.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Add("Content-Length", strconv.Itoa(len(data.Encode())))

	client := &http.Client{}
	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}

	return parseAndPrintAccessToken(body)
}

// GenerateJWTToken generates a JWT token, sends it to the server, and returns the parsed response
func GenerateJWTToken(privateKeyPath string, publicKeyPath string, clientID string, resourceID string, baseURL string) (map[string]interface{}, error) {
	privateKey, err := LoadPrivateKey(privateKeyPath)
	if err != nil {
		return nil, fmt.Errorf("error loading private key: %v", err)
	}

	claims := jwt.MapClaims{
		"jti": "id001",
		"aud": "/token",
		"sub": clientID,
		"iss": clientID,
		"iat": time.Now().Add(-6 * time.Hour).Unix(),
		"exp": time.Now().UTC().Add(1 * time.Hour).Unix(),
	}

	token := jwt.NewWithClaims(jwt.GetSigningMethod("RSA256"), claims)

	kid, err := getSha1Fingerprint(publicKeyPath)
	if err != nil {
		return nil, fmt.Errorf("error getting SHA1 fingerprint: %v", err)
	}
	token.Header["kid"] = kid

	tokenString, err := token.SignedString(privateKey)
	if err != nil {
		return nil, fmt.Errorf("error signing token: %v", err)
	}

	return sendTokenRequest(tokenString, clientID, resourceID, baseURL)
}
