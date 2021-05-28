import time
from threading import Thread
import queue
from math import ceil

from lib.file_manager import FileManager
from lib.package import Package, AbortPackage, Header
from lib.socket_udp import CONNECTION_TIMEOUT, CHUNK_SIZE
from lib.socket_udp import server_socket_udp
from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException
from lib.timer import Timer
from lib.exceptions import TimeOutException
from lib.client_udp_gbn import W_SIZE


class Connection_instance:
    def __init__(self, socket, address, fmanager, printer):
        self.socket = socket
        self.address = address
        self.fmanager = fmanager
        self.printer = printer
        self.running = False
        self.in_use_file_path = None
        self.pckg_queue = queue.Queue()

    def push(self, package):
        self.pckg_queue.put(package)
        self.last_active = time.time()

    def pull(self):
        package = self.pckg_queue.get()
        return package

    def start(self):
        self.running = True
        self.thread = Thread(target=self.dispatch)
        self.thread.start()

    def dispatch(self):
        start = time.time()
        self.printer.print_connection_established(self.address)
        try:
            first = self.pull()
            ptype = first.header.req

            self.printer.print_begin_transfer(first.header.name)
            if ptype == UPLOAD:
                self.do_upload(first)
            elif ptype == DOWNLOAD:
                self.do_download(first)

        except AbortedException:
            if self.in_use_file_path:
                self.fmanager.close_file(self.in_use_file_path)
            self.printer.print_connection_lost(self.address)

        self.printer.print_connection_finished(self.address)
        self.printer.print_duration(time.time() - start)

    def do_upload(self, firts_pckg):

        print('GBN and S&W upload')
        name = firts_pckg.header.name
        size = firts_pckg.header.filesz
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path

        last_recv_seqnum = -1
        package = firts_pckg
        transmition_complt = False
        while self.running and not transmition_complt:

            if package.header.seqnum == last_recv_seqnum + 1:
                finished, written = self.__reconstruct_file(package, path)
                self.printer.progressBar(written, size)
                last_recv_seqnum += 1

            self.socket.send_ack(last_recv_seqnum, self.address)

            if finished:
                self.fmanager.close_file(path)
                self.__close()
                transmition_complt = True
            else:
                package = self.pull()
        self.printer.print_upload_finished(name)

    def do_download(self, request):

        print('S&W download')
        name = request.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path
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
        self.fmanager.close_file(path)
        self.printer.print_download_finished(name)

    def is_active(self):
        return self.running

    def close(self):
        self.running = False

    def __reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def join(self):
        self.thread.join()


class Server_udp:
    def __init__(self, address, port, dir_addr, printer):
        self.address = address
        self.port = port
        self.active_connections = {}
        self.socket = None
        self.fmanager = FileManager(dir_addr)
        self.printer = printer

    def run(self):
        self.create_socket()
        self._setup_cleaner()
        self.listen()

    def create_socket(self):
        self.socket = server_socket_udp(self.address, self.port)
        self.socket.bind()

    def listen(self):
        self.printer.print_listening_on((self.address, self.port))
        while(True):
            try:
                package, address = self.socket.blocking_recv()
                self.demux(package, address)
            except ConnectionResetError:
                pass
            except KeyboardInterrupt:
                break
        self.socket.socket.close()

    def demux(self, package, address):
        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, addr):
        c = Server_udp_gbn(self.socket, addr, self.fmanager, self.printer)
        c.start()
        self.active_connections[addr] = c

    def _setup_cleaner(self):
        Thread(target=self._periodic_clean).start()

    def _periodic_clean(self):
        while True:
            time.sleep(CONNECTION_TIMEOUT)

            dead_connections = {}
            for addr, connection in self.active_connections.items():
                if not connection.is_active():
                    connection.push(AbortPackage())
                    connection.join()
                    self.printer.print_connection_stats(self.socket)
                    dead_connections[addr] = connection

            for addr in dead_connections:
                del self.active_connections[addr]


class Server_udp_gbn(Connection_instance):

    def __init__(self, address, port, fmanager, printer):
        super().__init__(address, port, fmanager, printer)

        self.window_base = 0
        self.last_sent_seqnum = -1
        self.seqnum_head = 0
        self.sendq = []

    def window_full(self):
        return (self.seqnum_head - self.window_base) == W_SIZE

    def fill_sending_queue(self, path, name, filesz):

        file_finished = False
        while not self.window_full() and not file_finished:
            header = Header(self.seqnum_head, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')

            if (len(payload) == 0):
                file_finished = True
            else:
                pkg = Package(header, payload)
                self.sendq.append(pkg)
                self.seqnum_head += 1

    def send_queued_unsent(self):
        amount_sent = 0
        unsent = self.sendq[self.last_sent_seqnum + 1: self.seqnum_head]
        for pkg in unsent:
            self.socket.send(pkg, self.address)
            amount_sent += 1

        self.last_sent_seqnum += amount_sent

    def recv_acks(self, timer):
        try:
            while self.running:
                pkg = self.socket.blocking_recv_through(self.pckg_queue)
                if pkg.is_ack():
                    ack_seqnum = pkg.header.seqnum
                    self.window_base = ack_seqnum
                    timer.reset()
        except AbortedException:
            pass

    def send_all_queued(self):
        unkacked = self.sendq[self.window_base: self.seqnum_head]
        for pkg in unkacked:
            self.socket.send(pkg, self.address)

    def do_download(self, request):

        print('GBN download')
        name = request.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path
        filesz = self.fmanager.get_size(path)
        end_seqnum = ceil(filesz/CHUNK_SIZE)

        try:
            timer = Timer(CONNECTION_TIMEOUT)
            acks_listener = Thread(args=[timer], target=self.recv_acks)
            acks_listener.start()

            timer.start()
            transfer_complt = False
            while not transfer_complt and self.running:
                try:
                    timer.update()
                    self.fill_sending_queue(path, name, filesz)
                    self.send_queued_unsent()

                    if self.window_base == (end_seqnum - 1):
                        transfer_complt = True

                    b_arrived = self.last_sent_seqnum * CHUNK_SIZE
                    self.printer.progressBar(b_arrived, filesz)
                except TimeOutException:
                    timer.reset()
                    self.send_all_queued()
            timer.stop()
        except (KeyboardInterrupt, ConnectionResetError, AbortedException):
            timer.stop()

        print(self.window_base)
        b_arrived = self.last_sent_seqnum * CHUNK_SIZE
        self.printer.progressBar(b_arrived, filesz)
        self.printer.print_download_finished(name)

        self.close()
        acks_listener.join()
        self.fmanager.close_file(path)
