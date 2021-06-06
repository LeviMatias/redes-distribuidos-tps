from lib.package import Package, Header, UPLOAD
from lib.exceptions import AbortedException
from lib.socket_udp import client_socket_udp, CHUNK_SIZE
import time


class Client_udp:
    def __init__(self, address, port, fmanager, printer):

        self.socket = client_socket_udp(address, port)
        self.address = (address, port)
        self.fmanager = fmanager
        self.printer = printer

    def upload(self, path, name):
        self._data_transfer(path, name, self.do_upload)

    def download(self, path, name):
        self._data_transfer(path, name, self.do_download)

    def _data_transfer(self, path, name, protocol):
        start = time.time()
        try:
            self.printer.print_begin_transfer(name)
            protocol(path, name)
        except FileNotFoundError:
            self.printer.print_file_not_found(path)
        except AbortedException:
            self.printer.print_connection_lost(self.address)
        finally:
            self.fmanager.close_file(path)
            self.printer.print_connection_finished(self.address)
            self.printer.print_duration(time.time() - start)
            self.printer.print_connection_stats(self.socket)

    def do_upload(self, path, name):

        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz:
            header = Header(seqnum, UPLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)

            self.socket.reliable_send(package, self.address)

            sent += len(payload)
            seqnum += 1
            self.printer.progressBar(sent, filesz)

        self.printer.print_upload_finished(name)

    def do_download(self, path, name):
        last_recv_seqnum = -1

        req_pkg = Package.create_download_request(name)
        package = self.socket.reliable_send_and_recv(req_pkg, self.address)
        last_recv_seqnum += 1
        finished, written = self.__reconstruct_file(package, path)

        if finished:
            self.fmanager.close_file(path)

        while not finished:
            self.socket.send_ack(last_recv_seqnum, self.address)
            self.printer.progressBar(written, package.header.filesz)
            package = self.socket.listen_for_next_from(last_recv_seqnum)
            last_recv_seqnum += 1

            finished, written = self.__reconstruct_file(package, path)

        for _ in range(0, 3):
            self.socket.send_ack(last_recv_seqnum, self.address)
        self.printer.print_download_finished(name)

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz, written
