https://chatgpt.com/c/d5baa8f2-9a61-46aa-bb16-ea570ad916ff#:~:text=Here%27s%20the%20full%20code%20with%20directory%20structure%3A

https://chatgpt.com/c/d5baa8f2-9a61-46aa-bb16-ea570ad916ff#:~:text=Sure%2C%20here%27s%20how%20you%20can%20modify%20the%20mqmonth.go%20file%20to%20include%20three%20functions%20for%20different%20HTTP%20methods%20(GET%2C%20POST%2C%20and%20DELETE)%20with%20endpoints%20/get_qmgrs%2C%20/post_gmrs%2C%20and%20/delete_wmgrs%20respectively.%20These%20functions%20will%20call%20the%20API%2C%20pass%20the%20JWT%20token%20in%20the%20headers%2C%20and%20return%20the%20JSON%20response%3A
package main

import (
	"bytes"
	"crypto/rsa"
	"crypto/sha1"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/dgrijalva/jwt-go"
)

var (
	private *rsa.PrivateKey
	public  *rsa.PublicKey
)

func main() {
	// Load private key
	privateKey, err := loadPrivateKey("path/to/private.pem")
	if err != nil {
		fmt.Printf("Error loading private key: %v\n", err)
		return
	}
	private = privateKey

	// Generate JWT token
	tokenString, err := generateJWTToken()
	if err != nil {
		fmt.Printf("Error generating JWT token: %v\n", err)
		return
	}
	fmt.Printf("Token String: %v\n", tokenString)

	// Send token to the server and get response
	responseBody, err := sendTokenRequest(tokenString)
	if err != nil {
		fmt.Printf("Error sending token request: %v\n", err)
		return
	}
	fmt.Printf("Token Body: %v---%T\n", string(responseBody), responseBody)

	// Parse and print the access token
	parseAndPrintAccessToken(responseBody)
}

func loadPrivateKey(path string) (*rsa.PrivateKey, error) {
	priv, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return jwt.ParseRSAPrivateKeyFromPEM(priv)
}

func generateJWTToken() (string, error) {
	data := map[string]interface{}{
		"jti": "id001",
		"aud": "/token",
		"sub": "88153",
		"iss": "88153",
	}
	cl := jwt.MapClaims{}
	for k, v := range data {
		cl[k] = v
	}
	cl["iat"] = time.Now().Add(-6 * time.Hour).Unix()
	cl["exp"] = time.Now().UTC().Add(1 * time.Hour).Unix()
	token := jwt.NewWithClaims(jwt.GetSigningMethod("RSA256"), cl)
	kid := getSha1Fingerprint()
	token.Header["kid"] = kid

	return token.SignedString(private)

	// claims := jwt.MapClaims{
	// 	"jti": "id001",
	// 	"aud": "/token",
	// 	"sub": "88153",
	// 	"iss": "88153",
	// 	"iat": time.Now().Add(-6 * time.Hour).Unix(),
	// 	"exp": time.Now().UTC().Add(1 * time.Hour).Unix(),
	// }

	// token := jwt.NewWithClaims(jwt.GetSigningMethod("RSA256"), claims)

	// kid := getSha1Fingerprint()
	// token.Header["kid"] = kid

	// return token.SignedString(private)
}

func sendTokenRequest(token string) ([]byte, error) {
	data := url.Values{}
	data.Set("grant_type", "client")
	data.Set("clnt_id", "123")
	data.Set("resource", "qwer")
	data.Set("client_assertion", strings.TrimSpace(token))

	client := &http.Client{}
	req, err := http.NewRequest("POST", "url", strings.NewReader(data.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Add("Content-Length", strconv.Itoa(len(data.Encode())))

	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	return io.ReadAll(res.Body)
}

func parseAndPrintAccessToken(body []byte) {
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		fmt.Printf("Error parsing response body: %v\n", err)
		return
	}
	if accessToken, ok := result["access_token"]; ok {
		fmt.Printf("Access Token: %v\n", accessToken)
	} else {
		fmt.Println("Access Token not found in response")
	}
}

func getSha1Fingerprint() string {
	pemContent, err := os.ReadFile("path/to/public.pem")
	if err != nil {
		panic(err)
	}
	block, _ := pem.Decode(pemContent)
	if block == nil {
		panic("failed to parse PEM file")
	}
	cert, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		panic(err)
	}
	fingerprint := sha1.Sum(cert.Raw)
	var buf bytes.Buffer
	for i, f := range fingerprint {
		if i > 0 {
			fmt.Fprintf(&buf, ":")
		}
		fmt.Fprintf(&buf, "%02x", f)
	}
	fmt.Printf("Fingerprint: %v\n", buf.String())
	return strings.ReplaceAll(buf.String(), ":", "")
}
