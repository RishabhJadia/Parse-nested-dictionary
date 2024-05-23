package main

import (
    "crypto/rsa"
    "crypto/sha256"
    "encoding/hex"
    "encoding/pem"
    "fmt"
    "io/ioutil"
    "log"
    "strings"
    "time"

    "github.com/golang-jwt/jwt/v4"
)

// ReadPrivateKey reads the RSA private key from a PEM file
func ReadPrivateKey(filePath string) (*rsa.PrivateKey, error) {
    privateKeyPEM, err := ioutil.ReadFile(filePath)
    if err != nil {
        return nil, fmt.Errorf("failed to read private key file: %v", err)
    }

    privateKey, err := jwt.ParseRSAPrivateKeyFromPEM(privateKeyPEM)
    if err != nil {
        return nil, fmt.Errorf("failed to parse private key: %v", err)
    }

    return privateKey, nil
}

// ReadPublicKey reads the RSA public key from a PEM file
func ReadPublicKey(filePath string) (*rsa.PublicKey, error) {
    publicKeyPEM, err := ioutil.ReadFile(filePath)
    if err != nil {
        return nil, fmt.Errorf("failed to read public key file: %v", err)
    }

    block, _ := pem.Decode(publicKeyPEM)
    if block == nil || block.Type != "PUBLIC KEY" {
        return nil, fmt.Errorf("failed to decode public key PEM")
    }

    publicKey, err := jwt.ParseRSAPublicKeyFromPEM(publicKeyPEM)
    if err != nil {
        return nil, fmt.Errorf("failed to parse public key: %v", err)
    }

    return publicKey, nil
}

func generateToken(privateKey *rsa.PrivateKey, kid string) (string, error) {
    // Create a new token object
    token := jwt.NewWithClaims(jwt.SigningMethodRS256, jwt.MapClaims{
        "iss": "your-issuer",         // Issuer
        "sub": "user-id-123",         // Subject
        "aud": "your-audience",       // Audience
        "exp": time.Now().Add(time.Hour * 72).Unix(), // Expiration Time
        "iat": time.Now().Unix(),     // Issued At
    })

    // Set the "kid" in the header
    token.Header["kid"] = kid

    // Sign the token with the private key
    tokenString, err := token.SignedString(privateKey)
    if err != nil {
        return "", fmt.Errorf("failed to sign token: %v", err)
    }

    return tokenString, nil
}

func computeKidFromPublicKey(publicKey *rsa.PublicKey) (string, error) {
    // Encode the public key to PEM format
    pubASN1, err := x509.MarshalPKIXPublicKey(publicKey)
    if err != nil {
        return "", fmt.Errorf("failed to marshal public key: %v", err)
    }

    // Compute the SHA-256 fingerprint of the public key
    hash := sha256.Sum256(pubASN1)
    fingerprint := hex.EncodeToString(hash[:])
    kid := strings.ReplaceAll(fingerprint, ":", "")

    return kid, nil
}

func verifyToken(tokenString string, publicKey *rsa.PublicKey) (*jwt.Token, error) {
    // Parse and validate the token
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return publicKey, nil
    })

    if err != nil {
        return nil, fmt.Errorf("failed to parse token: %v", err)
    }

    return token, nil
}

func main() {
    // Read the private key from the file
    privateKey, err := ReadPrivateKey("path/to/private/key.pem")
    if err != nil {
        log.Fatalf("Failed to read private key: %v", err)
    }

    // Read the public key from the file
    publicKey, err := ReadPublicKey("path/to/public/key.pem")
    if err != nil {
        log.Fatalf("Failed to read public key: %v", err)
    }

    // Compute the kid from the public key
    kid, err := computeKidFromPublicKey(publicKey)
    if err != nil {
        log.Fatalf("Failed to compute kid: %v", err)
    }

    // Generate the token
    tokenString, err := generateToken(privateKey, kid)
    if err != nil {
        log.Fatalf("Failed to generate token: %v", err)
    }

    fmt.Println("Generated Token:", tokenString)
    fmt.Println("Key ID (kid):", kid)

    // Verify the token
    token, err := verifyToken(tokenString, publicKey)
    if err != nil {
        log.Fatalf("Failed to verify token: %v", err)
    }

    if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
        fmt.Println("Token is valid")
        fmt.Println("Claims:", claims)
    } else {
        fmt.Println("Invalid token")
    }
}
