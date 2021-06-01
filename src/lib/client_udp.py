from lib.package import Package, Header, UPLOAD
from lib.exceptions import AbortedException, TimeOutException
from lib.socket_udp import client_socket_udp
from lib.socket_udp import CHUNK_SIZE, MAX_TIMEOUTS, CONNECTION_TIMEOUT
import time
from lib.timer import Timer


class Client_udp:
    def __init__(self, address, port, fmanager, printer):

        self.socket = client_socket_udp(address, port)
        self.address = (address, port)
        self.fmanager = fmanager
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
        except (AbortedException, ConnectionResetError):
            self.printer.print_connection_lost(self.address)
        except KeyboardInterrupt:
            pass
        except FileNotFoundError:
            self.printer.print_file_not_found(path)
        finally:
            self.printer.print_connection_finished(self.address)
            self.printer.print_duration(time.time() - start)
            self.close()

    def do_upload(self, path, name):

        self.printer._print('S&W upload')
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
            self.printer.conn_stats(self.socket, sent, size)

        self.fmanager.close_file(path)
        self.printer.print_upload_finished(name)

    def do_download(self, path, name):

        self.printer._print('GBN and S&W download')
        last_recv_seqnum = -1
        trnsmt_cmplt = False

        req_pkg = Package.create_download_request(name)
        pkg = self.socket.reliable_send_and_recv(req_pkg, self.address)
        filesz = pkg.header.filesz

        if pkg.header.seqnum == (last_recv_seqnum + 1):
            last_recv_seqnum += 1
            trnsmt_cmplt, written = self.__reconstruct_file(pkg, path)
            self.printer.conn_stats(self.socket, written, filesz)

            if trnsmt_cmplt:
                self.fmanager.close_file(path)

        self.socket.send_ack(last_recv_seqnum, self.address)

        timer = Timer(self.socket.timeout_limit)
        timer.start()
        timeouts = 0
        while self.running and not trnsmt_cmplt:
            try:
                pkg, _ = self.socket.blocking_recv(timer)
                timer.reset()

                if pkg.header.seqnum == (last_recv_seqnum + 1):
                    last_recv_seqnum += 1
                    trnsmt_cmplt, written = self.__reconstruct_file(pkg, path)
                    self.printer.conn_stats(self.socket, written, filesz)

                    if trnsmt_cmplt:
                        self.fmanager.close_file(path)

                self.socket.send_ack(last_recv_seqnum, self.address)
            except TimeOutException:
                timeouts += 1
                if timeouts >= MAX_TIMEOUTS:
                    raise AbortedException

        self.printer.print_download_finished(name)

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def close(self):
        self.running = False
        self.socket.close()
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)
        self.printer.print_program_closed()
