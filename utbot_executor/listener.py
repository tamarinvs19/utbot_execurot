from enum import Enum
import logging
import socket

from utbot_executor.deep_serialization.memory_objects import PythonSerializer
from utbot_executor.parser import parse_request, serialize_response
from utbot_executor.executor import PythonExecutor

logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(funcName)s - %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S',
        level=logging.INFO
        )

RECV_SIZE = 2048


class PythonExecuteServer:
    def __init__(
            self,
            hostname: str,
            port: int,
            ):
        logging.info('PythonExecutor is creating...')
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
                serialized_response = serialize_response(response)
                PythonSerializer().clear()

                bytes_data = serialized_response.encode()
                response_size = str(len(bytes_data))
                self.clientsocket.send(response_size.encode() + b'\n')

                sended_size = 0
                while len(bytes_data) > sended_size:
                    sended_size += self.clientsocket.send(bytes_data[sended_size:])

                logging.debug('Sent all data')
        logging.info('All done...')
