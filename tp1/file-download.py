import socket
import sys
from lib.client_tcp import Client
from lib.common import socket_tcp, FileManager
from lib.argument_parser import ArgParser


if __name__ == "__main__":

    ArgParser.check_client_side_args(sys.argv)

    host, port, file_name, file_path = ArgParser.parse_client_side(sys.argv)

    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.connect((host, port))

    if not file_path:
        file_path = FileManager('client').get_path(file_name)

    client = Client(socket_tcp(serv, (host, port)))
    client.download(file_path)
    client.close()
