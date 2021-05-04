import socket
from threading import Thread
from common_tcp import UPLOAD, DOWNLOAD, socket_tcp

BASE_PATH = "files-server/"
active_connections = []


class connection_instance:

    def __init__(self, cli):
        self.client = cli
        self.closed = False

    def upload(self):
        # wait for file name!
        name = str(self.client.recv_chunk())
        if name == "":
            return self.__close()

        self.client.send_ack()
        self.upfile = open(name, "w+")

        self.client.recv_to_file(self.upfile)

        self.upfile.close()
        self.upfile = None
        self.__close()

    def what_do(self):
        try:
            action = str(self.client.recv_chunk())
            self.client.send_ack()

            if action == UPLOAD:
                self.upload()
            elif action == DOWNLOAD:
                print("not done")
            else:
                print("Error: Invalid action " + action)
                self.__close()

        except ConnectionAbortedError:
            print("An error ocurred and the connection was closed")

    def run(self):
        self.thread = Thread(target=self.what_do)
        self.thread.start()

    # closes the socket, for internal use only
    def __close(self):
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
        if self.client.closed:
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

            ci = connection_instance(socket_tcp(conn, addr))
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
