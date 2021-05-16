import socket

class socket_udp:

    def __init__(self, socket):
        self.socket = socket

    def send(self, package):
        self.socket.send(package.encode())

    def recv(self, size, err_condition_lambda=(lambda: False)):
        while not err_condition_lambda():
             data, address = socket.recvfrom(size)
             if data:
                 return data, address

        raise ConnectionAbortedError



