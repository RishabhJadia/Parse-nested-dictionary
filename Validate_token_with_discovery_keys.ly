import requests
import jwt
from jwt.algorithms import RSAAlgorithm

def fetch_jwks(discovery_endpoint):
    response = requests.get(discovery_endpoint)
    return response.json()

def get_public_key(jwks_data, kid):
    for entry in jwks_data:
        for key in entry['keys']:
            if key['kid'] == kid:
                public_key = RSAAlgorithm.from_jwk(key)
                return public_key
    raise Exception('Public key not found.')

def validate_jwt(token, jwks_data, audience):
    headers = jwt.get_unverified_header(token)
    kid = headers['kid']
    public_key = get_public_key(jwks_data, kid)
    
    try:
        decoded_token = jwt.decode(token, public_key, algorithms=["RS256"], audience=audience)
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired.")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token.")

# Replace with your discovery endpoint and JWT token
discovery_endpoint = "https://your-discovery-endpoint/.well-known/jwks.json"
token = "your_jwt_token"
audience = "your_audience"

# Fetch JWKS data
jwks_data = fetch_jwks(discovery_endpoint)

# Validate the JWT token
try:
    decoded_token = validate_jwt(token, jwks_data, audience)
    print("Token is valid:", decoded_token)
except Exception as e:
    print(str(e))
