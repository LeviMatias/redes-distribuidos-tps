import socket
from threading import Thread

CHUNK_SIZE = 1024
OK_ACK = "Ok"
active_connections = []


class connection_instance:

    def __init__(self, cli, addr):
        print("connection with "+ addr[0] + ":" + str(addr[1]) + " started")
        self.client = cli
        self.addr = addr
        self.closed = False

    def receive(self):
        bytes_recv = 0
        size = int(self.client.recv(CHUNK_SIZE).decode())
        self.client.send(b"Ok")

        while bytes_recv < size:
            data = self.client.recv(CHUNK_SIZE)
            bytes_recv += len(data)
            print(str(data.decode()))

        self.__close()

    def run(self):
        self.thread = Thread(target=self.receive)
        self.thread.start()

    # closes the socket, for internal use only
    def __close(self):
        if self.closed:
            return

        addr = self.addr
        print("connection with " + addr[0] + ":" + str(addr[1]) + " finished")
        self.closed = True
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()

    # closes the socket and joins the thread
    # for external use only
    def close(self):
        self.__close()
        if self.thread:
            self.thread.join()
            self.thread = False

    # asks whether thread is done and joins it if necessary
    # for external use only
    def finished(self):
        if self.closed:
            self.close()
        return self.closed


def serve(host, port):
    addr = (host, port)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)
        sock.listen(1)
        print("listening on " + addr[0] + ":" + str(addr[1]))

        while True:
            conn, addr = sock.accept()
             # cull list from dead connections
            active_connections[:] = [c for c in active_connections
                                     if c.finished()]

            if not conn:
                break

            ci = connection_instance(conn, addr)
            ci.run()
            active_connections.append(ci)

    except KeyboardInterrupt:

        if sock:
            sock.close()
            for cli in active_connections:
                cli.close()

        print("goodbye")


if __name__ == "__main__":
    serve("localhost", 8080)
