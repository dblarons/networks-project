import flatbuffers
import time
import zmq

from registrar.models.client import Client
from registrar.models.room import Room
import registrar.config as config

import registrar.Registrar.Client
import registrar.Registrar.Command
import registrar.Registrar.CommandType
import registrar.Registrar.Room

PORT = '5556'

db = config.database
db.connect();

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % PORT)

while True:
    #  Wait for next request from client
    message = socket.recv()
    print("Received request: ", message)
    with db.transaction():
        Room.create(
            guid=message,
            name='barbaz')
    time.sleep(1)
    socket.send_string("World from %s" % PORT)
