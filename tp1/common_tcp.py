import socket
import os

UPLOAD = "Upload"
DOWNLOAD = "Download"
CHUNK_SIZE = 1024
OK_ACK = "Ok"


def progressBar(current, total, barLength=20):
    percent = float(current) * 100 / total
    arrow = '-' * int(percent/100 * barLength - 1) + '>'
    spaces = ' ' * (barLength - len(arrow))

    print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')


class socket_tcp:
    def __init__(self, conn, addr):
        print("connection with " + addr[0] + ":" + str(addr[1]) + " started")
        self.conn = conn
        self.addr = addr
        self.closed = False

    def recv(self):
        return self.conn.recv(CHUNK_SIZE).decode()

    def send(self, data):
        return self.conn.send(data.encode())

    def recive_file(self, file_name, size):

        file = FileManager.open_file(name=file_name, how='w+')

        bytes_recv = 0
        data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

        while bytes_recv < size and data:
            data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)
            progressBar(bytes_recv, size)

        file.close()

    def recv_and_reconstruct_file(self, file, bytes_recived):

        data = self.recv()
        bytes_recived += len(data)
        file.write(data.decode())
        return data, bytes_recived

    def send_file(self, file_name, size):

        file = FileManager.open_file(name=file_name, how='r')

        bytes_sent = 0
        data, bytes_sent = self.read_file_and_send(file, bytes_sent)

        while bytes_sent < size and data:
            data, bytes_sent = self.read_file_and_send(file, bytes_sent)
            progressBar(bytes_sent, size)

        file.close()

    def read_file_and_send(self, file, bytes_sent):

        data = file.read(CHUNK_SIZE)
        self.send(data)
        bytes_sent += len(data)
        return data, bytes_sent

    def wait_ack(self):
        ack = self.recv()
        if ack != OK_ACK:
            print("invalid ack received {}", ack.decode())
            return False
        return True

    def wait_for_request(self):
        return self._wait_for_string_msg()

    def wait_for_name(self):
        return self._wait_for_string_msg()

    def wait_for_size(self):
        size = int(self.recv())
        self.send_ack()
        return size

    def _wait_for_string_msg(self):
        msg = str(self.recv())
        if msg == "":
            raise(ConnectionAbortedError)
        self.send_ack()
        return msg

    def send_ack(self):
        self.send(OK_ACK)

    def send_size(self, file_name):
        size = FileManager.get_size(file_name)
        self.send(str(size))
        self.wait_ack()
        return size

    def close(self):
        if self.closed:
            return

        addr = self.addr
        print("connection with " + addr[0] + ":" + str(addr[1]) + " finished")
        self.closed = True
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()


class FileManager:

    BASE_PATH = "./files-client/"

    name_to_path = {
        "test.txt": "test.txt",
    }

    path_to_name = dict((v, k) for k, v in name_to_path.items())

    @staticmethod
    def get_name(path):
        return FileManager.path_to_name[path]

    @staticmethod
    def get_path(name):
        return FileManager.name_to_path[name]

    @staticmethod
    def open_file(how, name='', path=''):

        if name:
            path = FileManager.name_to_path[name]

        f = open(FileManager.get_absolute_path(path), how)

        return f

    @staticmethod
    def get_absolute_path(file_path):
        return FileManager.BASE_PATH + file_path

    @staticmethod
    def get_size(file_name):

        f = FileManager.open_file(name=file_name, how='r')

        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0, os.SEEK_SET)

        f.close()

        return size
