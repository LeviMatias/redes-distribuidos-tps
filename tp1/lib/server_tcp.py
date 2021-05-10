import socket
from threading import Thread
from lib.common import UPLOAD, DOWNLOAD, socket_tcp, FileManager, Printer


class connection_instance:

    def __init__(self, cli, dir_path):
        self.client = cli
        self.closed = False
        self.file_manager = FileManager('server', dir_path)

    def __server_upload_protocol(self):

        file_name = self.client.wait_for_name()
        size = self.client.wait_for_size()

        file = self.file_manager.open_file(name=file_name, how='w+')
        self.client.recv_file(file, size, from_host='server')
        file.close()

    def __server_download_protocol(self):

        file_name = self.client.wait_for_name()

        file = self.file_manager.open_file(name=file_name, how='r')
        size = self.file_manager.get_size(file)
        self.client.send_size(size)

        self.client.send_file(file, size, from_host='server')
        file.close()

    def dispatch_request(self, request):
        if request == UPLOAD:
            self.__server_upload_protocol()
        elif request == DOWNLOAD:
            self.__server_download_protocol()
        else:
            raise(ConnectionAbortedError)

    def listen_request(self):

        try:
            request = self.client.wait_for_request()
            request = self.dispatch_request(request)
        except ConnectionAbortedError:
            Printer.print_connection_aborted()
        finally:
            self.__close()

    def run(self):
        self.thread = Thread(target=self.listen_request)
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
        return self.client.closed


def serve(host, port, dir_path):
    addr = (host, port)
    active_connections = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)
        sock.listen(1)
        Printer.print_listening_on(addr)

        while True:
            conn, addr = sock.accept()
            # cull list from dead connections
            active_connections[:] = [c for c in active_connections
                                     if not c.finished()]

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