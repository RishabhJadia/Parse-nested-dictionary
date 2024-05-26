package jwt

import (
	"bytes"
	"crypto/rsa"
	"crypto/sha1"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"
	"strings"

	"github.com/dgrijalva/jwt-go"
)

func LoadPrivateKey(path string) (*rsa.PrivateKey, error) {
	priv, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return jwt.ParseRSAPrivateKeyFromPEM(priv)
}

func GetSha1Fingerprint(publickeypath string) string {
	pemContent, err := os.ReadFile(publickeypath)
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
