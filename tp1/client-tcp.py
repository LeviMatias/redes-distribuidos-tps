import os
import socket

CHUNK_SIZE = 16
OK_ACK = "Ok"


class Client:
    def __init__(self, addres_family, protocol):
        self.sock = socket.socket(addres_family, protocol)

    def connect(self, host, port):
        self.sock.connect((host, port))

    def send(self, file_path):

        f = open(file_path, 'rb')
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0, os.SEEK_SET)

        self.sock.send(str(size).encode())
        ack = self.sock.recv(CHUNK_SIZE)
        if ack.decode() != OK_ACK:
            print("invalid ack received {}", ack.decode())
            return exit()

        chunk = f.read(CHUNK_SIZE)
        while chunk:
            self.sock.send(chunk)
            chunk = f.read(CHUNK_SIZE)

        f.close()

    def close(self):
        self.sock.close()

    def progressBar(current, total, barLength = 20):
        percent = float(current) * 100 / total
        arrow   = '-' * int(percent/100 * barLength - 1) + '>'
        spaces  = ' ' * (barLength - len(arrow))

        print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')


if __name__ == "__main__":
    client = Client(socket.AF_INET, socket.SOCK_STREAM)

    host = '127.0.0.1'
    port = 8080

    client.connect(host, port)
    client.send("C:\\Users\\axelpm\\Desktop\\test.txt")
    client.close()
