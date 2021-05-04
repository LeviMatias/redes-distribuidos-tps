import os
import socket
from common_tcp import UPLOAD, CHUNK_SIZE, socket_tcp

BASE_PATH = "files-client/"


class Client:
    def __init__(self, serv):
        self.serv = serv

    def wait_ack(self):
        if not self.serv.wait_ack():
            print("do something?")

    def send(self, file_path):
        serv = self.serv
        # inform the server we want to upload
        serv.send_chunk(UPLOAD)
        self.wait_ack()

        # open the file and send the name to the server
        f = open(BASE_PATH + file_path, 'r')
        serv.send_chunk(file_path)
        self.wait_ack()

        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0, os.SEEK_SET)
        # send the file size to the server
        serv.send_chunk(str(size))
        self.wait_ack()

        # begin reading and sending data
        chunk = f.read(CHUNK_SIZE)
        bytes_read = 0
        self.progressBar(bytes_read, size)
        while chunk:
            serv.send_chunk(chunk)
            bytes_read += len(chunk)
            self.progressBar(bytes_read, size)
            chunk = f.read(CHUNK_SIZE)

        f.close()

    def close(self):
        self.serv.close()

    def progressBar(self, current, total, barLength=20):
        percent = float(current) * 100 / total
        arrow = '-' * int(percent/100 * barLength - 1) + '>'
        spaces = ' ' * (barLength - len(arrow))

        print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')


if __name__ == "__main__":
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 8080
    serv.connect((host, port))

    client = Client(socket_tcp(serv, (host, port)))
    client.send("test.txt")
    client.close()
