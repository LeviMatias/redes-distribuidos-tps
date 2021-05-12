import socket
import os
import time

UPLOAD = "Upload"
DOWNLOAD = "Download"
CHUNK_SIZE = 1024
OK_ACK = "Ok"


class socket_tcp:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.closed = False
        self.bytes_recv = 0
        self.bytes_sent = 0
        self.start_t = time.time()

    def recv(self):
        r = self.conn.recv(CHUNK_SIZE).decode()
        self.bytes_recv += len(r)
        return r

    def send(self, data):
        s = self.conn.send(data.encode())
        self.bytes_sent += len(s)
        return s

    def recv_file(self, file, size, progress=(lambda _x, _y: None)):

        bytes_recv = 0
        data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

        while bytes_recv < size and data:
            data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

            progress(bytes_recv, size)

    # recv bytes and write them into a buffer(file), update local byte counter
    def recv_and_reconstruct_file(self, file, bytes_recived):

        data = self.recv()
        bytes_recived += len(data)
        file.write(data)
        return data, bytes_recived

    def send_file(self, file, size, progress=(lambda _x, _y: None)):

        bytes_sent = 0
        data, bytes_sent = self.read_file_and_send(file, bytes_sent)

        while bytes_sent < size and data:
            data, bytes_sent = self.read_file_and_send(file, bytes_sent)

            progress(bytes_sent, size)

    # read a chunk from file buffer and send it thru the connection,
    #  update local counter
    def read_file_and_send(self, file, bytes_sent):

        data = file.read(CHUNK_SIZE)
        self.send(data)
        bytes_sent += len(data)
        return data, bytes_sent

    # wait for other side to send OK_ACK
    def wait_ack(self):
        ack = self.recv()
        if ack != OK_ACK:
            raise(ConnectionAbortedError)

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

    def send_size(self, size):
        self.send(str(size))
        self.wait_ack()

    # close the connection
    def close(self):
        if self.closed:
            return

        self.closed = True
        self.time_alive = time.time() - self.start
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()


class FileManager:

    def __init__(self, host, dir_path):
        self.CLIENT_BASE_PATH = "lib/files-client/"
        self.SERVER_BASE_PATH = dir_path
        self.name_to_path = {
            "from_client_test_upload.txt": "from_client_test_upload.txt",
            "from_server_test_download.txt": "from_server_test_download.txt",
            "client_large_file_upload.txt": "client_large_file_upload.txt"}
        self.path_to_name = dict((v, k) for k, v in self.name_to_path.items())
        self.host = host

    def get_name(self, path):
        return self.path_to_name[path]

    def get_path(self, name):
        return self.name_to_path[name]

    def get_absolute_path(self, file_path):

        if self.host == 'server':
            return self.SERVER_BASE_PATH + file_path
        elif self.host == 'client':
            return self.CLIENT_BASE_PATH + file_path
        else:
            raise(ConnectionAbortedError)

    def open_file(self, how, name='', path=''):

        if name:
            path = self.name_to_path[name]

        full_path = self.get_absolute_path(path)
        f = open(full_path, how)

        return f

    def get_size(self, file):

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0, os.SEEK_SET)

        return size
