from socket import AF_INET, SOCK_DGRAM, socket


class socket_udp:

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((self.address, self.port))

    def send(self, data, address):
        self.socket.sendto(data, address)

    def recv(self, size):
        return self.socket.recvfrom(size)
