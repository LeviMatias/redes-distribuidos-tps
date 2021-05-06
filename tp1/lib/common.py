import socket
import os
import traceback

UPLOAD = "Upload"
DOWNLOAD = "Download"
CHUNK_SIZE = 1024
OK_ACK = "Ok"


class socket_tcp:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.closed = False

        Printer.print_connection_established(addr)

    def recv(self):
        return self.conn.recv(CHUNK_SIZE).decode()

    def send(self, data):
        return self.conn.send(data.encode())

    def recv_file(self, file, size, from_host):

        bytes_recv = 0
        data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

        while bytes_recv < size and data:
            data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

            if from_host == 'client':
                Printer.progressBar(bytes_recv, size)

    def recv_and_reconstruct_file(self, file, bytes_recived):

        data = self.recv()
        bytes_recived += len(data)
        file.write(data)
        return data, bytes_recived

    def send_file(self, file, size, from_host):

        bytes_sent = 0
        data, bytes_sent = self.read_file_and_send(file, bytes_sent)

        while bytes_sent < size and data:
            data, bytes_sent = self.read_file_and_send(file, bytes_sent)

            if from_host == 'client':
                Printer.progressBar(bytes_sent, size)

    def read_file_and_send(self, file, bytes_sent):

        data = file.read(CHUNK_SIZE)
        self.send(data)
        bytes_sent += len(data)
        return data, bytes_sent

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

    def close(self):
        if self.closed:
            return

        addr = self.addr
        Printer.print_connection_finished(addr)
        self.closed = True
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


class Printer:

    @staticmethod
    def __print(msg):
        print(msg)
        print()

    @staticmethod
    def print_connection_aborted():
        Printer.__print('An error ocurred. Connection closed')
        traceback.print_exc()

    @staticmethod
    def print_file_not_found(path):
        Printer.__print('File not found at: ' + path)
        traceback.print_exc()

    @staticmethod
    def print_connection_established(addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " started"
        Printer.__print(msg)

    @staticmethod
    def print_connection_finished(addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " finished"
        Printer.__print(msg)

    @staticmethod
    def print_listening_on(addr):
        Printer.__print("listening on " + addr[0] + ":" + str(addr[1]))

    @staticmethod
    def progressBar(current, total, barLength=20):
        percent = float(current) * 100 / total
        arrow = '-' * int(percent/100 * barLength - 1) + '>'
        spaces = ' ' * (barLength - len(arrow))

        print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')
