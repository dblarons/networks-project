import flatbuffers
import zmq

import registrar.Registrar.Command
import registrar.Registrar.Message
import registrar.Registrar.List

from registrar.models.client import Client
from registrar.models.room import Room
import registrar.config as config

PORT = '5556'

db = config.database
db.connect();

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('tcp://*:%s' % PORT)

def build_command(builder, message_type, message):
    registrar.Registrar.Command.CommandStart(builder)
    registrar.Registrar.Command.CommandAddMessageType(
        builder, message_type)
    registrar.Registrar.Command.CommandAddMessage(builder, message)
    return registrar.Registrar.Command.CommandEnd(builder)

def build_list_message(builder, room_models):
    room_offsets = []
    for room in room_models:
        offset = room.serialize(builder)
        room_offsets.append(offset)

    registrar.Registrar.List.ListStartRoomsVector(builder, len(room_offsets))
    for offset in room_offsets:
        builder.PrependUOffsetTRelative(offset)
    rooms = builder.EndVector(len(room_offsets))

    registrar.Registrar.List.ListStart(builder)
    registrar.Registrar.List.ListAddRooms(builder, rooms)
    return registrar.Registrar.List.ListEnd(builder)

while True:
    #  Wait for next request from client
    request = socket.recv()

    Command = registrar.Registrar.Command.Command.GetRootAsCommand(request, 0)
    message_type = Command.MessageType()

    # Switch on the message type to send a response.
    builder = flatbuffers.Builder(1024)
    message_offset = 0
    if message_type == registrar.Registrar.Message.Message().List:
        print('SERVER: Received a List command')
        rooms = Room.select()
        message_offset = build_list_message(builder, rooms)

    offset = build_command(
        builder,
        registrar.Registrar.Message.Message().List,
        message_offset)

    builder.Finish(offset)
    response = builder.Output()
    socket.send(response)

    print('SERVER: Sent a response')

    # with db.transaction():
    #     Room.create(
    #         guid=message,
    #         name='barbaz')
