import os
import atexit
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


class server:

    def __init__(self):
        self.active_connections = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def serve(self, host, port):
        addr = (host, port)
        self.serving = True

        self.sock.bind(addr)
        self.sock.listen(1)
        print("listening on " + addr[0] + ":" + str(addr[1]))

        while self.serving:
            conn, addr = self.sock.accept()
            if not conn:
                break

            ci = connection_instance(conn, addr)
            ci.run()
            self.active_connections.append(ci)

    def run(self, host, port):
        self.thread = Thread(target=self.serve, args=(host, port))
        self.thread.start()

    def close(self):
        if self.thread and self.sock:
            self.serving = False
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.thread.join()

        for cli in self.active_connections:
            cli.close()


server = server()


def main():
    server.run("localhost", 8080)


def cleanup():
    server.close()

    print("goodbye")
    os.exit()


atexit.register(cleanup)


if __name__ == "__main__":
    main()
