import flatbuffers
import zmq

import registrar.Registrar.Client
import registrar.Registrar.Command
import registrar.Registrar.Create
import registrar.Registrar.List
import registrar.Registrar.Message

PORT = '5556'

context = zmq.Context()
print('Connecting to server...')
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:%s" % PORT)

# Build list request

def build_list_request(builder):
    registrar.Registrar.Command.CommandStart(builder)
    registrar.Registrar.Command.CommandAddMessageType(
        builder, registrar.Registrar.Message.Message().List)
    return registrar.Registrar.Command.CommandEnd(builder)

def read_list_response(command):
    union_list = registrar.Registrar.List.List()
    union_list.Init(command.Message().Bytes, command.Message().Pos)

    rooms_length = union_list.RoomsLength()
    for i in range(rooms_length):
        room = union_list.Rooms(i)
        print(room.Name())

def send_command(builder, offset):
    builder.Finish(offset)
    request = builder.Output()
    socket.send(request)
    response = socket.recv()
    return response

def build_create_request(builder):
    client_id = builder.CreateString('New client')
    ip = builder.CreateString('129.0.0.1')
    registrar.Registrar.Client.ClientStart(builder)
    registrar.Registrar.Client.ClientAddId(builder, client_id)
    registrar.Registrar.Client.ClientAddIp(builder, ip)
    registrar.Registrar.Client.ClientAddPort(builder, 1234)
    client = registrar.Registrar.Client.ClientEnd(builder)

    name = builder.CreateString('New room')
    registrar.Registrar.Create.CreateStart(builder)
    registrar.Registrar.Create.CreateAddName(builder, name)
    registrar.Registrar.Create.CreateAddClient(builder, client)
    message = registrar.Registrar.Create.CreateEnd(builder)

    registrar.Registrar.Command.CommandStart(builder)
    registrar.Registrar.Command.CommandAddMessageType(
        builder, registrar.Registrar.Message.Message().Create)
    registrar.Registrar.Command.CommandAddMessage(builder, message)
    return registrar.Registrar.Command.CommandEnd(builder)

builder = flatbuffers.Builder(1024)
offset = build_list_request(builder)

print('CLIENT: Sending a List request');
response = send_command(builder, offset)

command = registrar.Registrar.Command.Command.GetRootAsCommand(response, 0)

if command.MessageType() == registrar.Registrar.Message.Message().List:
    print('CLIENT: Received List response from server')
    read_list_response(command)
else:
    print('ERROR: Expected List message type but got another')

builder = flatbuffers.Builder(1024)
offset = build_create_request(builder)

print('CLIENT: Sending a Create request')
response = send_command(builder, offset)

command = registrar.Registrar.Command.Command.GetRootAsCommand(response, 0)

if command.MessageType() == registrar.Registrar.Message.Message().Create:
    print('CLIENT: Received Create response from server')
else:
    print('ERROR: Expected Create message type but got another')
