import zmq
import time
import sqlite3

conn = sqlite3.connect('registrar.db')

c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS peers (host text, port text)')
conn.commit()

PORT = '5556'

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % PORT)

def store_in_db(conn):
    c = conn.cursor()
    c.execute("INSERT INTO peers VALUES ('127.0.0.1', '1234')")
    conn.commit()

while True:
    #  Wait for next request from client
    message = socket.recv()
    print("Received request: ", message)
    store_in_db(conn)
    time.sleep(1)
    socket.send_string("World from %s" % PORT)
