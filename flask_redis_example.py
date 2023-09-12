####requirements.txt
#async-timeout==4.0.3
#blinker==1.6.2
#cachelib==0.10.2
#click==8.1.7
#colorama==0.4.6
#Flask==2.3.3
#flask-redis==0.4.0
#Flask-Session==0.5.0
#Flask-SQLAlchemy==2.4.4
#gunicorn==19.9.0
#itsdangerous==2.1.2
#Jinja2==3.1.2
#MarkupSafe==2.1.3
#redis==5.0.0
#SQLAlchemy==1.3.22
#Werkzeug==2.3.7
####----------------------------------------------------------
from flask import Flask, session
from flask_redis import FlaskRedis
from flask_session import Session
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Redis configuration
app.config['REDIS_URL'] = 'redis://localhost:6379'  # Replace with your Redis server URL

# Configure Flask-Redis
redis_store = FlaskRedis(app)

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis_store
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Set session timeout to 1 hour
Session(app)


@app.route('/')
def index():
    # Store data in the session
    session['username'] = 'John'
    return 'Session data set'


@app.route('/profile')
def profile():
    # Retrieve data from the session
    username = session.get('username')
    return f'Username: {username}'


@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    return 'Logged out'


if __name__ == '__main__':
    app.run()
