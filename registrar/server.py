import flatbuffers
import zmq

from registrar.models.client import Client
from registrar.models.room import Room
import registrar.config as config

import registrar.Registrar.Command
import registrar.Registrar.Message

PORT = '5556'

db = config.database
db.connect();

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('tcp://*:%s' % PORT)

def build_list_response(builder):
    registrar.Registrar.Command.CommandStart(builder)
    registrar.Registrar.Command.CommandAddMessageType(
        builder, registrar.Registrar.Message.Message().ListCmd)
    return registrar.Registrar.Command.CommandEnd(builder)

while True:
    #  Wait for next request from client
    request = socket.recv()
    print('SERVER: Received message')

    builder = flatbuffers.Builder(1024)
    offset = build_list_response(builder)
    builder.Finish(offset)
    response = builder.Output()

    socket.send(response)

    print('SERVER: Sent a response')

    # with db.transaction():
    #     Room.create(
    #         guid=message,
    #         name='barbaz')
