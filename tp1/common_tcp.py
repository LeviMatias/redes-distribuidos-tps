import socket
UPLOAD = "Upload"
DOWNLOAD = "Download"
CHUNK_SIZE = 1024
OK_ACK = "Ok"


class socket_tcp:
    def __init__(self, conn, addr):
        print("connection with " + addr[0] + ":" + str(addr[1]) + " started")
        self.conn = conn
        self.addr = addr
        self.closed = False

    def send_ack(self):
        self.conn.send(OK_ACK.encode())

    def wait_ack(self):
        ack = self.conn.recv(CHUNK_SIZE)
        if ack.decode() != OK_ACK:
            print("invalid ack received {}", ack.decode())
            return False
        return True

    def ask_size(self):
        size = int(self.conn.recv(CHUNK_SIZE).decode())
        self.send_ack()
        return size

    def recv_to_file(self, upfile):
        bytes_recv = 0
        size = self.ask_size()
        data = "data"

        while bytes_recv < size and data != "":
            data = self.conn.recv(CHUNK_SIZE).decode()
            bytes_recv += len(data)
            upfile.write(data)

    def send_from_file(self, file):
        self.conn.sendall(file)

    def recv_chunk(self):
        return self.conn.recv(CHUNK_SIZE).decode()

    def send_chunk(self, data):
        return self.conn.send(data.encode())

    def close(self):
        if self.closed:
            return

        addr = self.addr
        print("connection with " + addr[0] + ":" + str(addr[1]) + " finished")
        self.closed = True
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()
