import flatbuffers
import sys
import zmq

import registrar.Registrar.Command
import registrar.Registrar.Create
import registrar.Registrar.Join
import registrar.Registrar.Message

from .utils import send_request, serialize_mock_client, build_command, read_list_response

SUB_PORT = '5555'
REQ_PORT = '5556'

context = zmq.Context()

print('Connecting to server...')
req_socket = context.socket(zmq.REQ)
req_socket.connect("tcp://localhost:%s" % REQ_PORT)

sub_socket = context.socket(zmq.SUB)
sub_socket.connect('tcp://localhost:%s' % SUB_PORT)

def build_create_request(builder):
    client = serialize_mock_client(builder)

    name = builder.CreateString('New room')
    registrar.Registrar.Create.CreateStart(builder)
    registrar.Registrar.Create.CreateAddName(builder, name)
    registrar.Registrar.Create.CreateAddClient(builder, client)
    return registrar.Registrar.Create.CreateEnd(builder)

def read_create_response(command):
    union_create = registrar.Registrar.Create.Create()
    union_create.Init(command.Message().Bytes, command.Message().Pos)

    room = union_create.Room()
    print('CLIENT: Created room with name ' + str(room.Name()))
    return room.Guid()

def build_join_request(builder, guid):
    guid = builder.CreateString(guid)
    client = serialize_mock_client(builder)

    registrar.Registrar.Join.JoinStart(builder)
    registrar.Registrar.Join.JoinAddGuid(builder, guid)
    registrar.Registrar.Join.JoinAddClient(builder, client)
    return registrar.Registrar.Join.JoinEnd(builder)

def read_join_response(command):
    union_join = registrar.Registrar.Join.Join()
    union_join.Init(command.Message().Bytes, command.Message().Pos)

    room = union_join.Room()
    print('CLIENT: Joined room with name ' + str(room.Name()))

    clients_length = union_join.ClientsLength()
    print('CLIENT: Joined room that has ' + str(clients_length) + ' other clients')
    for i in range(clients_length):
        client = union_join.Clients(i)
        print('CLIENT: Client ' + str(i) + ' in room has ip ' + str(client.Ip()))

############ LIST REQUEST ############

builder = flatbuffers.Builder(1024)
offset = build_command(
    builder,
    registrar.Registrar.Message.Message().List,
    0)

print('CLIENT: Sending a List request');
response = send_request(builder, req_socket, offset)

command = registrar.Registrar.Command.Command.GetRootAsCommand(response, 0)

first_room_guid = None
if command.MessageType() == registrar.Registrar.Message.Message().List:
    print('CLIENT: Received List response from server')
    first_room_guid = read_list_response(command)
else:
    print('ERROR: Expected List message type but got another')

############ CREATE REQUEST ############

builder = flatbuffers.Builder(1024)
create_offset = build_create_request(builder)
offset = build_command(
    builder,
    registrar.Registrar.Message.Message().Create,
    create_offset)

print('CLIENT: Sending a Create request')
response = send_request(builder, req_socket, offset)

command = registrar.Registrar.Command.Command.GetRootAsCommand(response, 0)

if command.MessageType() == registrar.Registrar.Message.Message().Create:
    print('CLIENT: Received Create response from server')
    room_guid = read_create_response(command)
    sub_socket.setsockopt(smq.SUBSCRIBE, room_guid.encode('utf-8'))
else:
    print('ERROR: Expected Create message type but got another')

############ JOIN REQUEST ############

if first_room_guid is None:
    sys.exit()

print('CLIENT: Joining room with guid: ' + str(first_room_guid))

builder = flatbuffers.Builder(1024)
join_offset = build_join_request(builder, first_room_guid)
offset = build_command(
    builder,
    registrar.Registrar.Message.Message().Join,
    join_offset)

print('CLIENT: Sending a Join request')
response = send_request(builder, req_socket, offset)

command = registrar.Registrar.Command.Command.GetRootAsCommand(response, 0)

if command.MessageType() == registrar.Registrar.Message.Message().Join:
    read_join_response(command)
    print('CLIENT: Received Join response from server')
else:
    print('ERROR: Expected Join message type but got another')
