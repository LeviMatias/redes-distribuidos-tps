import socket
from threading import Thread
from lib.common import UPLOAD, DOWNLOAD, socket_tcp, FileManager


class connection_instance:

    def __init__(self, cli, dir_path, printer):
        self.client = cli
        self.closed = False
        self.printer = printer
        self.file_manager = FileManager('server', dir_path)
        printer.print_connection_established(cli.addr)

    # server side of the upload protocol
    def _server_upload_protocol(self):

        file_name = self.client.wait_for_name()
        size = self.client.wait_for_size()

        file = self.file_manager.open_file(name=file_name, how='wb')
        self.client.recv_file(file, size)
        file.close()

    # server side of the download protocol
    def _server_download_protocol(self):

        file_name = self.client.wait_for_name()

        file = self.file_manager.open_file(name=file_name, how='rb')
        size = self.file_manager.get_size(file)
        self.client.send_size(size)

        self.client.send_file(file, size)
        file.close()

    # choose handler for the request
    def dispatch_request(self, request):
        if request == UPLOAD:
            self._server_upload_protocol()
        elif request == DOWNLOAD:
            self._server_download_protocol()
        else:
            raise(ConnectionAbortedError)

    # listen for what the client wants to do
    def listen_request(self):

        try:
            request = self.client.wait_for_request()
            request = self.dispatch_request(request)
        except (ConnectionAbortedError, ConnectionResetError):
            self.printer.print_connection_aborted()
        finally:
            self._close()

    def run(self):
        self.thread = Thread(target=self.listen_request)
        self.thread.start()

    # closes the socket, for internal use only
    def _close(self):
        self.client.close()
        self.printer.print_connection_finished(self.client.addr)
        self.printer.print_connection_stats(self.client.bytes_sent,
                                            self.client.bytes_recv,
                                            self.client.time_alive)

    # closes the socket and joins the thread
    # for external use only
    def close(self):
        self._close()
        if self.thread:
            self.thread.join()
            self.thread = False

    # asks whether thread is done and joins it if necessary
    # for external use only
    def finished(self):
        if self.client.closed:
            self.close()
        return self.client.closed


def serve(host, port, dir_path, printer):
    addr = (host, port)
    active_connections = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)
        sock.listen(1)
        printer.print_listening_on(addr)

        while True:
            conn, addr = sock.accept()
            # cull list from dead connections
            active_connections[:] = [c for c in active_connections
                                     if not c.finished()]

            if not conn:
                break

            ci = connection_instance(socket_tcp(conn, addr), dir_path, printer)
            ci.run()
            active_connections.append(ci)

    except KeyboardInterrupt:

        if sock:
            sock.close()
            for cli in active_connections:
                cli.close()
