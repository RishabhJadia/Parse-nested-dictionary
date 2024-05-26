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
	var err error
	var priv []byte
	priv, err = os.ReadFile("pki")
	if err != nil {
		panic(err)
	}
	private, err = jwt.ParseRSAPrivateKeyFromPEM(priv)
	if err != nil {
		panic(err)
	}

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
	kid := getSha1()
	token.Header["kid"] = kid

	tokenString, err := token.SignedString(private)
	fmt.Printf("Token String--->%v\n", tokenString)
	GetTokenbyte(tokenString)
}

func GetTokenbyte(token string) []byte {
	data := url.Values{}
	data.Set("grant_type", "client")
	data.Set("clnt_id", "123")
	data.Set("resource", "qwer")
	data.Set("client_assertion", strings.TrimSpace(token))

	client := &http.client{}
	r, err := http.NewRequest("POST", "url", strings.NewReader(data.Encode()))
	if err != nil {
		fmt.Println(err)
	}
	r.Header.Add("Content-Type", "application/json")
	r.Header.Add("Content-Length", strconv.Itoa(len(data.Encode())))

	res, err := client.err
	if err != nil {
		fmt.Println(err)
	}
	defer res.Body.Close()
	body, err := io.ReadAll(res.Body)
	if err != nil {
		fmt.Println(err)
	}
	fmt.Printf("Token BOdy: %v---%T", string(body), body)
	result := map[string]any{}
	json.Unmarshal(body, &result)
	fmt.Printf("%v", result["access_token"])
}

func getSha1() string {
	pemContent, err := os.ReadFile("/pki")
	if err != nil {
		panic(err)
	}
	block, _ := pem.Decode(pemContent)
	if block == nil {
		panic("faied tp parse pem file")
	}
	cert, err := x509.ParseCertificate(block.Bytes)
	if cert != nil {
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
	fmt.Printf("Fingerprint %v", buf.String())
	return strings.ReplaceAll(buf.String(), ":", "")
}
