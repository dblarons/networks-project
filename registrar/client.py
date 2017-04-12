import zmq

import registrar.Registrar.Client
import registrar.Registrar.Command
import registrar.Registrar.CommandType
import registrar.Registrar.Room

PORT = '5556'

context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:%s" % PORT)

#  Do 10 requests, waiting each time for a response
for request in range(1,10):
    print("Sending request ", request,"...")
    socket.send_string("Hello" + str(request))
    #  Get the reply.
    message = socket.recv()
    print("Received reply ", request, "[", message, "]")
