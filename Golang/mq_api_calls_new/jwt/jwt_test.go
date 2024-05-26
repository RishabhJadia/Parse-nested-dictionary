package jwt

import (
	"crypto/rsa"
	"errors"
	"io"
	"net/http"
	"path/filepath"
	"strings"
	"testing"

	"github.com/dgrijalva/jwt-go"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mocked dependencies
type MockedFileReader struct {
	mock.Mock
}

func (m *MockedFileReader) ReadFile(path string) ([]byte, error) {
	args := m.Called(path)
	return args.Get(0).([]byte), args.Error(1)
}

type MockedHTTPClient struct {
	mock.Mock
}

func (m *MockedHTTPClient) Do(req *http.Request) (*http.Response, error) {
	args := m.Called(req)
	return args.Get(0).(*http.Response), args.Error(1)
}

var mockedFileReader = new(MockedFileReader)
var mockedHTTPClient = new(MockedHTTPClient)

// Override the os.ReadFile and http.DefaultClient.Do with mocks
var readFile = func(path string) ([]byte, error) {
	return mockedFileReader.ReadFile(path)
}

var httpClient = func(req *http.Request) (*http.Response, error) {
	return mockedHTTPClient.Do(req)
}

func init() {
	// Replace os.ReadFile with the mock
	osReadFile = readFile
	// Replace http.DefaultClient.Do with the mock
	httpDo = httpClient
}

func TestLoadPrivateKey(t *testing.T) {
	tests := []struct {
		name        string
		privatePath string
		fileContent []byte
		fileError   error
		expectedKey *rsa.PrivateKey
		expectedErr error
	}{
		{
			name:        "Success",
			privatePath: "mqadmin_private.pem",
			fileContent: []byte(`-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1J6F3xIzi1ZlLZ/Jf/Y3W0hGvK8uBfR1X7q0UmhPt5DbQm50
-----END RSA PRIVATE KEY-----`),
			expectedKey: &rsa.PrivateKey{}, // Replace with the actual key if necessary
			expectedErr: nil,
		},
		{
			name:        "File not found",
			privatePath: "non_existent.pem",
			fileContent: nil,
			fileError:   errors.New("file not found"),
			expectedKey: nil,
			expectedErr: errors.New("file not found"),
		},
		{
			name:        "Invalid private key format",
			privatePath: "invalid_private.pem",
			fileContent: []byte("invalid_key"),
			expectedKey: nil,
			expectedErr: jwt.ErrKeyMustBePEMEncoded,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockedFileReader.On("ReadFile", filepath.Join("pki", tt.privatePath)).Return(tt.fileContent, tt.fileError).Once()
			key, err := LoadPrivateKey(tt.privatePath)
			if tt.expectedErr != nil {
				assert.Nil(t, key)
				assert.Error(t, err)
				assert.Equal(t, tt.expectedErr.Error(), err.Error())
			} else {
				assert.NotNil(t, key)
				assert.NoError(t, err)
			}
			mockedFileReader.AssertExpectations(t)
		})
	}
}

func TestGenerateJWTToken(t *testing.T) {
	tests := []struct {
		name              string
		privateKeyPath    string
		publicKeyPath     string
		clientID          string
		resourceID        string
		fileContent       []byte
		fileError         error
		fingerprint       string
		fingerprintError  error
		tokenSigningError error
		httpResponse      *http.Response
		httpError         error
		expectedResponse  map[string]interface{}
		expectedErr       error
	}{
		{
			name:           "Success",
			privateKeyPath: "mqadmin_private.pem",
			publicKeyPath:  "mqadmin_public.pem",
			clientID:       "88153",
			resourceID:     "123456-ri",
			fileContent: []byte(`-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1J6F3xIzi1ZlLZ/Jf/Y3W0hGvK8uBfR1X7q0UmhPt5DbQm50
-----END RSA PRIVATE KEY-----`),
			fingerprint: "abc123",
			httpResponse: &http.Response{
				StatusCode: 200,
				Body:       io.NopCloser(strings.NewReader(`{"access_token": "token_value"}`)),
			},
			expectedResponse: map[string]interface{}{"access_token": "token_value"},
			expectedErr:      nil,
		},
		{
			name:           "File not found",
			privateKeyPath: "non_existent.pem",
			publicKeyPath:  "mqadmin_public.pem",
			clientID:       "88153",
			resourceID:     "123456-ri",
			fileError:      errors.New("file not found"),
			expectedErr:    errors.New("error loading private key: file not found"),
		},
		{
			name:             "Error getting fingerprint",
			privateKeyPath:   "mqadmin_private.pem",
			publicKeyPath:    "invalid_public.pem",
			clientID:         "88153",
			resourceID:       "123456-ri",
			fingerprintError: errors.New("failed to parse PEM file"),
			expectedErr:      errors.New("error getting SHA1 fingerprint: failed to parse PEM file"),
		},
		{
			name:              "Token signing error",
			privateKeyPath:    "mqadmin_private.pem",
			publicKeyPath:     "mqadmin_public.pem",
			clientID:          "88153",
			resourceID:        "123456-ri",
			tokenSigningError: errors.New("signing error"),
			expectedErr:       errors.New("error signing token: signing error"),
		},
		{
			name:           "HTTP error",
			privateKeyPath: "mqadmin_private.pem",
			publicKeyPath:  "mqadmin_public.pem",
			clientID:       "88153",
			resourceID:     "123456-ri",
			httpError:      errors.New("network error"),
			expectedErr:    errors.New("network error"),
		},
		{
			name:           "Invalid HTTP response",
			privateKeyPath: "mqadmin_private.pem",
			publicKeyPath:  "mqadmin_public.pem",
			clientID:       "88153",
			resourceID:     "123456-ri",
			httpResponse: &http.Response{
				StatusCode: 500,
				Body:       io.NopCloser(strings.NewReader(`Internal Server Error`)),
			},
			expectedErr: errors.New("Error parsing response body: unexpected end of JSON input"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockedFileReader.On("ReadFile", filepath.Join("pki", tt.privateKeyPath)).Return(tt.fileContent, tt.fileError).Once()
			mockedFileReader.On("ReadFile", filepath.Join("pki", tt.publicKeyPath)).Return(tt.fileContent, tt.fileError).Once()
			if tt.fingerprintError == nil {
				mockedFileReader.On("ReadFile", filepath.Join("pki", tt.publicKeyPath)).Return([]byte(`-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1J6F3xIzi1ZlLZ/Jf/Y3
W0hGvK8uBfR1X7q0UmhPt5DbQm50-----END PUBLIC KEY-----`), nil).Once()
			}
			if tt.tokenSigningError == nil {
				mockedFileReader.On("ReadFile", filepath.Join("pki", tt.privateKeyPath)).Return([]byte(`-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1J6F3xIzi1ZlLZ/Jf/Y3W0hGvK8uBfR1X7q0UmhPt5DbQm50
-----END RSA PRIVATE KEY-----`), nil).Once()
			}
			mockedHTTPClient.On("Do", mock.Anything).Return(tt.httpResponse, tt.httpError).Once()

			response, err := GenerateJWTToken(tt.privateKeyPath, tt.publicKeyPath, tt.clientID, tt.resourceID, "https://example.com")

			if tt.expectedErr != nil {
				assert.Nil(t, response)
				assert.Error(t, err)
				assert.Equal(t, tt.expectedErr.Error(), err.Error())
			} else {
				assert.NotNil(t, response)
				assert.NoError(t, err)
				assert.Equal(t, tt.expectedResponse, response)
			}
			mockedFileReader.AssertExpectations(t)
			mockedHTTPClient.AssertExpectations(t)
		})
	}
}
