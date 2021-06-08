import queue
import time
from threading import Thread


from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException, ConnectionInterrupt
from lib.exceptions import TimeOutException
from lib.package import Package, Header
from lib.socket_udp import server_socket_udp
from lib.common import CHUNK_SIZE, MAX_TIMEOUTS, CONNECTION_TIMEOUT
from lib.logger import Logger
from lib.timer import Timer


class Connection_instance:
    def __init__(self, address, fmanager, printer):
        self.socket = server_socket_udp(address[0], address[1])
        self.address = address
        self.fmanager = fmanager
        self.logger = Logger('./lib/files-server/')
        self.printer = printer
        self.running = False
        self.timeouts = 0
        self.in_use_file_path = None
        self.pckg_queue = queue.Queue()

    def push(self, package):
        self.pckg_queue.put(package)
        self.last_active = time.time()
        self.timeouts = 0

    def pull(self):
        package = self.pckg_queue.get()
        package.validate()
        self.socket.update_recv_stats(package)
        return package

    def start(self):
        self.running = True
        self.thread = Thread(target=self.dispatch)
        self.thread.start()

    def dispatch(self):
        start = time.time()
        self.printer.print_connection_established(self.address)
        aborted = False
        try:
            first = self.pull()
            ptype = first.header.req

            name = first.header.name
            path = self.fmanager.SERVER_BASE_PATH + name
            self.in_use_file_path = path

            self.printer.print_begin_transfer(first.header.name)
            if ptype == UPLOAD:
                self.do_upload(first, path, name)
            elif ptype == DOWNLOAD:
                self.do_download(first, path, name)

        except FileNotFoundError:
            self.printer.print_file_not_found(path)
        except (AbortedException, ConnectionResetError):
            self.printer.print_connection_lost(self.address)
            aborted = True
        except ConnectionInterrupt:
            self.printer.print_connection_interrupted(self.address)
            aborted = True
        finally:
            if not aborted:
                self.printer.print_connection_finished(self.address)
            self.printer.print_duration(time.time() - start)
            self.close()

    def do_upload(self, firts_pckg, path, name):

        self.printer._print('S&W upload')

        last_recv_seqnum = -1
        size = firts_pckg.header.filesz
        pkg = firts_pckg
        finished = False
        self.logger.log(str(pkg.header.seqnum))
        while self.running and not finished:

            if pkg.header.seqnum == last_recv_seqnum + 1:
                finished, written = self.__reconstruct_file(pkg, path)
                self.printer.print_progress(self.socket, written, size)
                last_recv_seqnum += 1

            self.socket.send_ack(last_recv_seqnum, self.address)
            self.logger.log("ack" + str(last_recv_seqnum))

            if not finished:
                pkg = self.socket.blocking_recv_through(self.pckg_queue)
                self.logger.log(str(pkg.header.seqnum))
            else:
                for _ in range(0, 3):
                    self.socket.send_ack(last_recv_seqnum, self.address)

    def do_download(self, request, path, name):

        self.printer._print('S&W download')

        filesz = self.fmanager.get_size(path)
        seqnum = request.header.seqnum
        bytes_sent = 0

        while bytes_sent < filesz:
            header = Header(seqnum, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)
            self.socket.reliable_send(package, self.address, self.pckg_queue)

            bytes_sent += len(payload)
            seqnum += 1
            self.printer.print_progress(self.socket, bytes_sent, filesz)
        self.printer.print_download_finished(name)

    def is_active(self):
        timed_out = time.time() - self.last_active > CONNECTION_TIMEOUT
        self.timeouts += 1 if timed_out else 0
        return self.timeouts <= MAX_TIMEOUTS

    def _reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def close(self):
        self.running = False
        self.logger.close()
        self.socket.close()
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)

    def join(self):
        self.thread.join()
