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
        self.running = True

    def upload(self, path, name):
        self._data_transfer(path, name, self.do_upload)

    def download(self, path, name):
        self._data_transfer(path, name, self.do_download)

    def _data_transfer(self, path, name, protocol):
        start = time.time()
        try:
            self.printer.print_begin_transfer(name)
            protocol(path, name)
        except AbortedException:
            self.fmanager.close_file(path)
            self.printer.print_connection_lost(self.address)
            self.socket.socket.close()

        self.printer.print_connection_finished(self.address)
        self.printer.print_duration(time.time() - start)
        self.printer.print_connection_stats(self.socket)

    def do_upload(self, path, name):

        print('S&W upload')
        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz:
            header = Header(seqnum, UPLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)

            self.socket.reliable_send(package, self.address)
            self.printer.progressBar(sent, filesz)

            sent += len(payload)
            seqnum += 1

        self.fmanager.close_file(path)
        self.printer.print_upload_finished(name)

    def do_download(self, path, name):

        print('GBN and S&W download')
        last_recv_seqnum = -1
        transmit_complt = False

        req_pkg = Package.create_download_request(name)
        pkg = self.socket.reliable_send_and_recv(req_pkg, self.address)

        if pkg.header.seqnum == (last_recv_seqnum + 1):
            last_recv_seqnum += 1
            transmit_complt, written = self.__reconstruct_file(pkg, path)
            self.printer.progressBar(written, pkg.header.filesz)

            if transmit_complt:
                self.fmanager.close_file(path)

        self.socket.send_ack(last_recv_seqnum, self.address)

        while not transmit_complt:

            pkg, _ = self.socket.blocking_recv()

            if pkg.header.seqnum == (last_recv_seqnum + 1):
                last_recv_seqnum += 1
                transmit_complt, written = self.__reconstruct_file(pkg, path)
                self.printer.progressBar(written, pkg.header.filesz)

                if transmit_complt:
                    self.fmanager.close_file(path)

            self.socket.send_ack(last_recv_seqnum, self.address)
        self.printer.print_download_finished(name)

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def close(self):
        self.socket.close()
        self.running = False