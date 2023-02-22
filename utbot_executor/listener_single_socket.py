from enum import Enum
import logging
import socket
import time

from utbot_executor.parser import parse_request, serialize_response
from utbot_executor.executor import PythonExecutor

logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(funcName)s - %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S',
        level=logging.INFO
        )


class SocketMode(Enum):
    COMMAND = 0  # 4 bytes
    SIZE = 1     # 16 bytes
    CONTENT = 2  # <= 2**128 bytes


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

        self.executor = PythonExecutor()

    def run(self):
        logging.info('PythonExecutor is ready...')
        # clientsocket, _ = self.serversocket.accept()
        # self.handler(clientsocket)
        # clientsocket.close()

    def handler(self, clientsocket: socket.socket):
        logging.info('Start working...')
        stop = False

        while not stop:
            clientsocket, _ = self.serversocket.accept()
            try:
                command = clientsocket.recv(4)
                if command == b'STOP':
                    stop = True
                elif command == b'PING':
                    size = str(4).rjust(16, "0")
                    clientsocket.sendall((size + "\n" + "PONG").encode())
                elif command == b'DATA':
                    message_body: bytes = b''
                    message_size = int(clientsocket.recv(16).decode())
                    while message_size > 0:
                        message = clientsocket.recv(2048)
                        logging.debug('Got data: %s', message.decode())
                        message_body += message
                        message_size -= len(message)

                    request = parse_request(message_body.decode())
                    response = self.executor.run_function(request)
                    logging.debug('Got response from executor')
                    serialized_response = serialize_response(response)
                    logging.debug('Serialized response')

                    bytes_data = bytes(serialized_response, "utf-8")
                    size = str(len(bytes_data)).rjust(16, "0") + '\n'
                    clientsocket.send(size.encode() + bytes_data)
                    logging.debug('Sent all data')
                else:
                    pass
            finally:
                clientsocket.close()

                # if mode == SocketMode.COMMAND:
                #     command, message = message[:4], message[4:]
                #     logging.debug('New command: %s', command.decode())
                #     if command == b'STOP':
                #         break
                #     if command == b'PING':
                #         size = str(4).rjust(16, "0")
                #         clientsocket.sendall((size + "\n" + "PONG").encode())
                #     elif command == b'DATA':
                #         mode = SocketMode.SIZE
                # elif mode == SocketMode.SIZE:
                #     message_size, message = int(message[:16]), message[16:]
                #     logging.debug('Got message size: %d bytes', message_size)
                #     mode = SocketMode.CONTENT
                # elif mode == SocketMode.CONTENT:
                #     message_body += message
                #     message = b''
                #     logging.debug(
                #         'Update content, current size: %d / %d bytes',
                #         len(message_body),
                #         message_size,
                #     )
                #
                #     if len(message_body) == message_size:
                #         request = parse_request(message_body.decode())
                #         response = self.executor.run_function(request)
                #         logging.debug('Got response')
                #         serialized_response = serialize_response(response)
                #         logging.debug('Serialized response')
                #
                #         bytes_data = bytes(serialized_response, "utf-8")
                #         size = str(len(bytes_data)).rjust(16, "0") + '\n'
                #         print(size)
                #         clientsocket.send(size.encode() + bytes_data)
                #         logging.debug('Sent all data')
                #
                #         message_body = b''
                #         mode = SocketMode.COMMAND

        logging.info('All done...')


