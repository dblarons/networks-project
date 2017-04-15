import flatbuffers
import zmq

from registrar.models.client import Client
from registrar.models.room import Room
import registrar.config as config

import registrar.Registrar.Client
import registrar.Registrar.Command
import registrar.Registrar.Message
import registrar.Registrar.Room
import registrar.Registrar.Response
import registrar.Registrar.ListCmd

PORT = '5556'

db = config.database
db.connect();

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('tcp://*:%s' % PORT)

def build_list_response(builder, rooms_model):
    room_offsets = []
    for room in rooms_model:
        offset = serialize_room(builder, room)
        room_offsets.append(offset)

    registrar.Registrar.Response.ResponseStartRoomsVector(builder, len(room_offsets))
    for offset in room_offsets:
        builder.PrependUOffsetTRelative(offset)
    rooms = builder.EndVector(len(room_offsets))

    registrar.Registrar.Response.ResponseStart(builder)
    registrar.Registrar.Response.ResponseAddRooms(builder, rooms)
    response = registrar.Registrar.Response.ResponseEnd(builder)

    registrar.Registrar.ListCmd.ListCmdStart(builder)
    registrar.Registrar.ListCmd.ListCmdAddResponse(builder, response)
    list_cmd = registrar.Registrar.ListCmd.ListCmdEnd(builder)

    registrar.Registrar.Command.CommandStart(builder)
    registrar.Registrar.Command.CommandAddMessageType(
        builder, registrar.Registrar.Message.Message().ListCmd)
    registrar.Registrar.Command.CommandAddMessage(builder, list_cmd)
    return registrar.Registrar.Command.CommandEnd(builder)

def serialize_room(builder, room):
    client_offsets = []
    for client in room.clients:
        offset = serialize_client(builder, client)
        client_offsets.append(offset)

    guid = builder.CreateString(room.guid)
    name = builder.CreateString(room.name)

    registrar.Registrar.Room.RoomStartClientsVector(builder, len(client_offsets))
    for offset in client_offsets:
        builder.PrependUOffsetTRelative(offset)
    clients = builder.EndVector(len(client_offsets))

    registrar.Registrar.Room.RoomStart(builder)
    registrar.Registrar.Room.RoomAddGuid(builder, guid)
    registrar.Registrar.Room.RoomAddName(builder, name)
    registrar.Registrar.Room.RoomAddClients(builder, clients)

    return registrar.Registrar.Room.RoomEnd(builder)

def serialize_client(builder, client):
    client_id = builder.CreateString(client.internal_name)
    ip = builder.CreateString(client.ip)
    registrar.Registrar.Client.ClientStart(builder)
    registrar.Registrar.Client.ClientAddId(builder, client_id)
    registrar.Registrar.Client.ClientAddIp(builder, ip)
    registrar.Registrar.Client.ClientAddPort(builder, client.port)
    return registrar.Registrar.Client.ClientEnd(builder)

while True:
    #  Wait for next request from client
    request = socket.recv()

    Command = registrar.Registrar.Command.Command.GetRootAsCommand(request, 0)
    message_type = Command.MessageType()

    # Switch on the message type to send a response.
    builder = flatbuffers.Builder(1024)
    offset = 0
    if message_type == registrar.Registrar.Message.Message().ListCmd:
        print('SERVER: Received a ListCmd command')
        rooms = Room.select()
        offset = build_list_response(builder, rooms)

    builder.Finish(offset)
    response = builder.Output()
    socket.send(response)

    print('SERVER: Sent a response')

    # with db.transaction():
    #     Room.create(
    #         guid=message,
    #         name='barbaz')
