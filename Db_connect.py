autosys-metadata/
│
├── autosys_db/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── middleware.py
│   ├── token_manager.py
│   ├── db_connection_manager.py
│   ├── scheduler.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   └── views.py
│   └── ...
├── autosys_metadata/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py

# autosys_db/token_manager.py
import os
import time

TOKEN_EXPIRY_TIME = 3600  # 1 hour expiration

def generate_token():
    # Implement your X.509 token generation logic here
    # This is just a placeholder for demonstration
    token = "new_token"  # Replace with actual token generation logic
    os.environ['COCKROACH_TOKEN'] = token
    os.environ['TOKEN_GENERATED_TIME'] = str(time.time())
    return token

def get_token():
    return os.getenv('COCKROACH_TOKEN', generate_token())


# autosys_db/db_connection_manager.py
import os
import time
import threading
from django.db import close_old_connections
from .token_manager import generate_token

class ConnectionScheduler(threading.Thread):
    def run(self):
        while True:
            token_generated_time = float(os.getenv('TOKEN_GENERATED_TIME', time.time()))

            # Check if the token is about to expire
            if time.time() - token_generated_time > (TOKEN_EXPIRY_TIME - 300):  # 5 minutes buffer
                print("Token is about to expire, generating a new one.")
                generate_token()
                close_old_connections()  # Close old DB connections

            time.sleep(60)  # Sleep for a minute before checking again


# autosys_db/middleware.py
from django.db import close_old_connections

class ConnectionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        close_old_connections()  # Ensure old DB connections are closed
        response = self.get_response(request)
        return response


# autosys_metadata/settings.py
import os
from pathlib import Path
from autosys_db.token_manager import generate_token
from autosys_db.db_connection_manager import ConnectionScheduler

# Basic Django settings omitted for brevity

# Initial token generation
generate_token()

# Start the connection scheduler in a separate thread
connection_scheduler = ConnectionScheduler()
connection_scheduler.daemon = True  # Ensure the thread exits when the main program exits
connection_scheduler.start()

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database_name',
        'USER': 'your_database_user',
        'PASSWORD': os.getenv('COCKROACH_TOKEN', generate_token()),  # Dynamic password from token
        'HOST': 'your_host',
        'PORT': '26257',
    }
}
