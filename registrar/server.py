import flatbuffers
import uuid
import zmq

import registrar.Registrar.Command
import registrar.Registrar.Create
import registrar.Registrar.Join
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

def build_join_message(builder, room, clients):
    client_offsets = []
    for client in clients:
        offset = client.serialize(builder)
        client_offsets.append(offset)

    room_offset = room.serialize(builder)

    registrar.Registrar.Join.JoinStartClientsVector(builder, len(client_offsets))
    for offset in client_offsets:
        builder.PrependUOffsetTRelative(offset)
    client_vector_offset = builder.EndVector(len(client_offsets))

    registrar.Registrar.Join.JoinStart(builder)
    registrar.Registrar.Join.JoinAddRoom(builder, room_offset)
    registrar.Registrar.Join.JoinAddClients(builder, client_vector_offset)
    return registrar.Registrar.Join.JoinEnd(builder)

while True:
    #  Wait for next request from client
    request = socket.recv()

    Command = registrar.Registrar.Command.Command.GetRootAsCommand(request, 0)

    # Switch on the message type to send a response.
    builder = flatbuffers.Builder(1024)
    message_offset = 0
    message_type = Command.MessageType()
    if message_type == registrar.Registrar.Message.Message().List:
        print('SERVER: Received a List command')
        rooms = Room.select()
        message_offset = build_list_message(builder, rooms)
    elif message_type == registrar.Registrar.Message.Message().Create:
        print('SERVER: Received a Create command')
        union_create = registrar.Registrar.Create.Create()
        union_create.Init(Command.Message().Bytes, Command.Message().Pos)
        client = union_create.Client()
        with db.transaction():
            room = Room.create(guid=uuid.uuid1(), name=union_create.Name())
            Client.create(
                internal_name=client.Id(),
                ip=client.Ip(),
                room=room.id,
                port=client.Port())
    elif message_type == registrar.Registrar.Message.Message().Join:
        print('SERVER: Received a Join command')
        union_join = registrar.Registrar.Join.Join()
        union_join.Init(Command.Message().Bytes, Command.Message().Pos)
        guid = union_join.Guid()
        client = union_join.Client()
        room = Room.get(Room.guid == guid)

        # Send room and existing clients to the requester
        message_offset = build_join_message(builder, room, room.clients)

        # Add the requester to the list of clients
        with db.transaction():
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
