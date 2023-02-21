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

RECV_SIZE = 2048


class PythonExecuteServer:
    def __init__(
            self,
            hostname: str,
            port: int,
            ):
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientsocket.connect((hostname, port))
        self.executor = PythonExecutor()

    def run(self) -> None:
        logging.info('PythonExecutor is ready...')
        try:
            self.handler()
        finally:
            self.clientsocket.close()

    def handler(self) -> None:
        logging.info('Start working...')

        while True:
            command = self.clientsocket.recv(4)

            if command == b'STOP':
                break
            if command == b'DATA':
                message_size = int(self.clientsocket.recv(16).decode())
                logging.debug('Got message size: %d bytes', message_size)
                message_body = b''

                while len(message_body) < message_size:
                    message = self.clientsocket.recv(
                            min(RECV_SIZE, message_size - len(message_body))
                            )
                    message_body += message
                    logging.debug(
                        'Update content, current size: %d / %d bytes',
                        len(message_body),
                        message_size,
                    )

                request = parse_request(message_body.decode())
                response = self.executor.run_function(request)
                logging.debug('Got response')
                serialized_response = serialize_response(response)
                logging.debug('Serialized response')

                bytes_data = serialized_response.encode()
                response_size = str(len(bytes_data)).rjust(16, "0")
                self.clientsocket.send(response_size.encode())
                logging.debug('Sent size: %s', response_size)

                sended_size = 0
                while len(bytes_data) > sended_size:
                    response_bytes = bytes_data[
                            sended_size : min(sended_size+RECV_SIZE, len(bytes_data))
                            ]
                    sended_size += len(response_bytes)
                    self.clientsocket.send(response_bytes)
                logging.debug('Sent all data')
        logging.info('All done...')
