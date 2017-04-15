import flatbuffers
import zmq

import registrar.Registrar.Command
import registrar.Registrar.Message
import registrar.Registrar.Response
import registrar.Registrar.ListCmd

PORT = '5556'

context = zmq.Context()
print('Connecting to server...')
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:%s" % PORT)

# Build list request

def build_list_request(builder):
    registrar.Registrar.Command.CommandStart(builder)
    registrar.Registrar.Command.CommandAddMessageType(
        builder, registrar.Registrar.Message.Message().ListCmd)
    return registrar.Registrar.Command.CommandEnd(builder)

def read_list_response(command):
    union_list = registrar.Registrar.ListCmd.ListCmd()
    union_list.Init(command.Message().Bytes, command.Message().Pos)

    list_response = union_list.Response()

    rooms_length = list_response.RoomsLength()
    for i in range(rooms_length):
        room = list_response.Rooms(i)
        print(room.Name())

def send_command(builder, offset):
    builder.Finish(offset)
    request = builder.Output()
    socket.send(request)
    response = socket.recv()
    return response

builder = flatbuffers.Builder(1024)
offset = build_list_request(builder)

print('CLIENT: Sending a request');
response = send_command(builder, offset)
print('Got a response')

command = registrar.Registrar.Command.Command.GetRootAsCommand(response, 0)

if command.MessageType() == registrar.Registrar.Message.Message().ListCmd:
    print("CLIENT: Received list response from server")
    read_list_response(command)
