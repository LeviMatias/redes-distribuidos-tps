from lib.package import Package, Header, UPLOAD
from lib.exceptions import AbortedException, TimeOutException
from lib.common import CHUNK_SIZE, MAX_TIMEOUTS
from lib.socket_udp import client_socket_udp
from lib.logger import Logger
from lib.timer import Timer
import time


class Client_udp:
    def __init__(self, address, port, fmanager, printer):

        self.socket = client_socket_udp(address, port)
        self.address = (address, port)
        self.fmanager = fmanager
        self.logger = Logger('./lib/files-client/')
        self.printer = printer
        self.running = True
        self.in_use_file_path = None

    def upload(self, path, name):
        self._data_transfer(path, name, self.do_upload)

    def download(self, path, name):
        self._data_transfer(path, name, self.do_download)

    def _data_transfer(self, path, name, protocol):
        start = time.time()
        self.in_use_file_path = path
        try:
            self.printer.print_begin_transfer(name)
            protocol(path, name)
        except FileNotFoundError:
            self.printer.print_file_not_found(path)
        except AbortedException:
            self.printer.print_connection_lost(self.address)
        finally:
            self.close()
            self.printer.print_connection_finished(self.address)
            self.printer.print_duration(time.time() - start)

    def do_upload(self, path, name):

        self.printer._print('S&W upload')

        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz and self.running:
            header = Header(seqnum, UPLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)

            self.socket.reliable_send(package, self.address, self.logger)

            sent += len(payload)
            seqnum += 1
            self.printer.print_progress(self.socket, sent, filesz)

        self.printer.print_upload_finished(name)

    def do_download(self, path, name):

        self.printer._print('S&W and GBN download')
        last_recv_seqnum = -1
        trnsmt_cmplt = False

        req_pkg = Package.create_download_request(name)
        pkg = self.socket.reliable_send_and_recv(req_pkg, self.address)
        self.socket.update_recv_stats(pkg)
        self.logger.log(str(pkg.header.seqnum))
        filesz = pkg.header.filesz

        if pkg.header.seqnum == (last_recv_seqnum + 1):
            last_recv_seqnum += 1
            trnsmt_cmplt, written = self.__reconstruct_file(pkg, path)
            self.printer.print_progress(self.socket, written, filesz)

        self.socket.send_ack(last_recv_seqnum, self.address)
        self.logger.log("ack" + str(last_recv_seqnum))

        timer = Timer(self.socket.timeout_limit, TimeOutException)
        while self.running and not trnsmt_cmplt:
            try:
                timer.start()
                pkg, _ = self.socket.blocking_recv(timer)
                timer.stop()
                timeouts = 0
                self.logger.log(str(pkg.header.seqnum))

                if pkg.header.seqnum == (last_recv_seqnum + 1):
                    last_recv_seqnum += 1
                    trnsmt_cmplt, written = self.__reconstruct_file(pkg, path)
                    self.printer.print_progress(self.socket, written, filesz)

                self.socket.send_ack(last_recv_seqnum, self.address)
                self.logger.log("ack" + str(last_recv_seqnum))

            except TimeOutException:
                timeouts += 1
                if timeouts >= MAX_TIMEOUTS:
                    raise AbortedException

        for _ in range(0, 3):
            self.socket.send_ack(last_recv_seqnum, self.address)
            self.logger.log("ack" + str(last_recv_seqnum))

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def close(self):
        self.logger.close()
        self.running = False
        self.socket.close()
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)
