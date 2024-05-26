package jwt

import (
	"mq_api_calls/jwt/key"
	"time"

	"github.com/dgrijalva/jwt-go"
)

func GenerateJWTToken(clientID, resourceID, privateKeyPath string, publicKeyPath string) (string, error) {
	privateKey, err := key.LoadPrivateKey(privateKeyPath)
	if err != nil {
		return "", err
	}

	claims := jwt.MapClaims{
		"client_id":   clientID,
		"resource_id": resourceID,
		"iat":         time.Now().Unix(),
		"exp":         time.Now().Add(1 * time.Hour).Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
	kid := key.GetSha1Fingerprint(publicKeyPath)
	token.Header["kid"] = kid

	return token.SignedString(privateKey)
}
