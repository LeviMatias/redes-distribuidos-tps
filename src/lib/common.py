import socket
import time

UPLOAD = "Upload"
DOWNLOAD = "Download"
CHUNK_SIZE = 1024
OK_ACK = "Ok"
ABORT = 'Abort'


class socket_tcp:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.closed = False
        self.bytes_recv = 0
        self.bytes_sent = 0
        self.start_t = time.time()

    def recv_encoded_bytes(self):
        r = self.conn.recv(CHUNK_SIZE)
        self.bytes_recv += len(r)
        return r

    def recv(self):
        return self.recv_encoded_bytes().decode()

    def send_encoded_bytes(self, bytes):
        s = self.conn.send(bytes)
        self.bytes_sent += s
        return s

    def send(self, data):
        return self.send_encoded_bytes(data.encode())

    def recv_file(self, file, size, progress=(lambda _x, _y: None)):

        bytes_recv = 0
        data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

        while bytes_recv < size and data:
            data, bytes_recv = self.recv_and_reconstruct_file(file, bytes_recv)

            progress(bytes_recv, size)

    # recv bytes and write them into a buffer(file), update local byte counter
    def recv_and_reconstruct_file(self, file, bytes_recived):

        data = self.recv_encoded_bytes()
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
        self.send_encoded_bytes(data)
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
        self.time_alive = time.time() - self.start_t
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()
