import flatbuffers
import uuid
import zmq

import registrar.Registrar.Command
import registrar.Registrar.Create
import registrar.Registrar.List
import registrar.Registrar.Message

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

def build_list_message(builder, rooms):
    room_offsets = []
    for room in rooms:
        offset = room.serialize(builder)
        room_offsets.append(offset)

    registrar.Registrar.List.ListStartRoomsVector(builder, len(room_offsets))
    for offset in room_offsets:
        builder.PrependUOffsetTRelative(offset)
    room_vector_offset = builder.EndVector(len(room_offsets))

    registrar.Registrar.List.ListStart(builder)
    registrar.Registrar.List.ListAddRooms(builder, room_vector_offset)
    return registrar.Registrar.List.ListEnd(builder)

while True:
    #  Wait for next request from client
    request = socket.recv()

    Command = registrar.Registrar.Command.Command.GetRootAsCommand(request, 0)

    # Switch on the message type to send a response.
    builder = flatbuffers.Builder(1024)
    message_offset = 0
    message_type = None
    if Command.MessageType() == registrar.Registrar.Message.Message().List:
        print('SERVER: Received a List command')
        rooms = Room.select()
        message_type = registrar.Registrar.Message.Message().List
        message_offset = build_list_message(builder, rooms)
    elif Command.MessageType() == registrar.Registrar.Message.Message().Create:
        print('SERVER: Received a Create command')
        message_type = registrar.Registrar.Message.Message().Create
        with db.transaction():
            union_create = registrar.Registrar.Create.Create()
            union_create.Init(Command.Message().Bytes, Command.Message().Pos)
            client = union_create.Client()
            room = Room.create(guid=uuid.uuid1(), name=union_create.Name())
            Client.create(
                internal_name=client.Id(),
                ip=client.Ip(),
                room=room.id,
                port=client.Port())


    offset = build_command(
        builder,
        message_type,
        message_offset)

    builder.Finish(offset)
    response = builder.Output()
    socket.send(response)

    print('SERVER: Sent a response')

    # with db.transaction():
    #     Room.create(
    #         guid=message,
    #         name='barbaz')
