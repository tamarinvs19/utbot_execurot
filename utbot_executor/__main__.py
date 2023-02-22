import argparse
import logging

from utbot_executor.listener import PythonExecuteServer


def main(hostname: str, port: int):
    server = PythonExecuteServer(hostname, port)
    server.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'UtBot Python Executor',
        description = 'Listen socket stream and execute function value',
        )
    parser.add_argument('hostname')
    parser.add_argument('port')
    args = parser.parse_args()
    main(args.hostname, int(args.port))
