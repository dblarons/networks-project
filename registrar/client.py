import flatbuffers
import zmq

import registrar.Registrar.Command
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
        builder, registrar.Registrar.Message.Message().ListCmd)
    return registrar.Registrar.Command.CommandEnd(builder)

def send_command(builder, offset):
    builder.Finish(offset)
    request = builder.Output()
    socket.send(request)
    response = socket.recv()
    return response

builder = flatbuffers.Builder(1024)
offset = build_list_request(builder)

print('CLIENT: Sending a request');
send_command(builder, offset)
print('Got a response')
