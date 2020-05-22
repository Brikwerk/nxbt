import time
import os

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet


app = Flask(__name__,
            static_url_path='',
            static_folder='static',)

# Configuring/retrieving secret key
secrets_path = os.path.join(
    os.path.dirname(__file__), "secrets.txt"
)
if not os.path.isfile(secrets_path):
    secret_key = os.urandom(24).hex()
    with open(secrets_path, "w") as f:
        f.write(secret_key)
else:
    secret_key = None
    with open(secrets_path, "r") as f:
        secret_key = f.read()
app.config['SECRET_KEY'] = secret_key

# Starting socket server with Flask app
sio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@sio.on('connect')
def on_connect():
    print("Connected")
    emit('my response', {'data': 'Connected'})


@sio.on('disconnect')
def on_disconnect():
    print("Disconnected")


@sio.on('message')
def handle_message(message):
    print("Elapsed Time", (time.time()*1000) - message["timestamp"])


if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
