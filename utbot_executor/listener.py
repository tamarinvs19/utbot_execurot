import argparse
import socket
import threading
import queue

from utbot_executor.parser import parse_request, serialize_response
from utbot_executor.executor import PythonExecutor


class PythonExecuteServer:
    def __init__(
            self,
            hostname: str,
            port: int,
            ):
        self.hostname = hostname
        self.port = port

        self.serversocket = socket.create_server((self.hostname, self.port), family=socket.AF_INET)
        self.serversocket.listen(1)

        self.counter = 0
        self.executor = PythonExecutor()

    def run(self):
        clientsocket, _ = self.serversocket.accept()
        self.handler(clientsocket)
        clientsocket.close()

    def handler(self, clientsocket: socket.socket):
        print('Start working...')
        message_body: bytes = b''
        while True:
            message = clientsocket.recv(2048)
            print('Got data: ', message)

            if message == b'STOP':
                break
            if message == b'PING':
                clientsocket.sendall(bytes("PONG\n", "utf-8"))
            elif message == b'END':
                request = parse_request(message_body.decode())
                response = self.executor.run_function(request)
                serialized_response = serialize_response(response)
                clientsocket.sendall(bytes(serialized_response, "utf-8") + b'\n')
                message_body = b''
            else:
                message_body += message

        print('All done...')


