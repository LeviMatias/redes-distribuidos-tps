import socket
from lib.client_tcp import Client
from lib.common_tcp import socket_tcp

if __name__ == "__main__":

    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 8080
    serv.connect((host, port))

    client = Client(socket_tcp(serv, (host, port)))
    client.upload("client_large_file_upload.txt")
    client.close()
