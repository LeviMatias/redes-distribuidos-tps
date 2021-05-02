import socket
from threading import Thread

CHUNK_SIZE = 1024


class connection_instance:

    def __init__(self, cli, conn, addr):
        self.client = cli
        self.addr = addr

    def receive(self):
        bytes_recv = 0
        size = int(self.client.recv(CHUNK_SIZE).decode())
        while bytes_recv < size:
            data = self.client.recv(CHUNK_SIZE)
            bytes_recv += len(data)
            print(str(data.decode()))

        self.close()

    def run(self):
        self.thread = Thread(target=self.receive)
        self.thread.start()

    def close(self):
        if self.closed:
            return

        self.closed = True
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
        if self.thread:
            self.thread.join()


active_connections = []


def serve():
    addr = ("localhost", 8080)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)
        sock.listen(1)
        print("listening on " + addr[0] + ":" + str(addr[1]))

        while True:
            conn, addr = sock.accept()
            if not conn:
                break

            ci = connection_instance(conn, addr)
            ci.run()
            active_connections.append(ci)

    except KeyboardInterrupt:

        if sock:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            for cli in active_connections:
                cli.close()

        print("goodbye")


if __name__ == "__main__":
    serve()
