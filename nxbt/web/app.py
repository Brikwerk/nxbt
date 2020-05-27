import json
import os

from ..nxbt import Nxbt
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import eventlet


app = Flask(__name__,
            static_url_path='',
            static_folder='static',)
nxbt = Nxbt()

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
sio = SocketIO(app, cookie=False)


@app.route('/')
def index():
    return render_template('index.html')


@sio.on('connect')
def on_connect():
    print("Connected")
    index = nxbt.create_controller()


@sio.on('disconnect')
def on_disconnect():
    print("Disconnected")


@sio.on('create_controller')
def on_create_controller():
    pass


@sio.on('input')
def handle_input(message):
    print(json.loads(message))


def start_web_app():
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
