import os
import atexit
import socket
from threading import Thread

CHUNCK_SIZE = 16

class Client:

    def __init__(self,addres_family=socket.AF_INET,protocol=socket.SOCK_STREAM):
        self.sock = socket.socket(addres_family,protocol)

    def connect(self,host,port):
        self.sock.connect((host,port))

    def send(self,file_path):

        f = open(file_path,'rb')
        f.seek(0,os.SEEK_END)
        size = f.tell()
        f.seek(0,os.SEEK_SET)

        self.sock.send(str(size).encode())

        while True:
            chunk = f.read(CHUNCK_SIZE)
            sock.send(chunk)

        f.close()

    def close():
        self.sock.close()


if __name__ == "__main__":
    
    client = Client()

    host = '127.0.0.1'
    port = 8081

    client.connect(host,port)
    client.send(u"C:\\Users\\axelpm\\Desktop\\test.txt")
    client.close()