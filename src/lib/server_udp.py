import time
from threading import Thread
import queue

from lib.file_manager import FileManager
from lib.package import Package, AbortPackage, Header
from lib.socket_udp import CONNECTION_TIMEOUT, MAX_TIMEOUTS, CHUNK_SIZE
from lib.socket_udp import server_socket_udp
from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException, ConnectionInterrupt
from lib.common import EXIT


class Connection_instance:
    def __init__(self, address, fmanager, printer):
        self.socket = server_socket_udp(address[0], address[1])
        self.address = address
        self.fmanager = fmanager
        self.printer = printer
        self.running = False
        self.timeouts = 0
        self.in_use_file_path = None
        self.pckg_queue = queue.Queue()

    def push(self, package):
        self.pckg_queue.put(package)
        self.last_active = time.time()

    def pull(self):
        package = self.pckg_queue.get()
        package.validate()
        self.socket.t_bytes_recv += len(package.payload) + package.header.size
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
        except ConnectionInterrupt:
            pass
        finally:
            if not aborted:
                self.printer.print_connection_finished(self.address)
            self.printer.print_connection_stats(self.socket)
            self.printer.print_duration(time.time() - start)
            self.close()

    def do_upload(self, firts_pckg, path, name):

        last_recv_seqnum = -1
        package = firts_pckg
        transmition_complt = False
        while self.running and not transmition_complt:

            if package.header.seqnum == last_recv_seqnum + 1:
                transmition_complt = self.__reconstruct_file(package, path)
                last_recv_seqnum += 1

            self.socket.send_ack(last_recv_seqnum, self.address)

            if not transmition_complt:
                package = self.pull()

    def do_download(self, request, path, name):

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

    def is_active(self):
        timed_out = time.time() - self.last_active > CONNECTION_TIMEOUT
        self.timeouts = self.timeouts + 1 if timed_out else 0
        return self.timeouts <= MAX_TIMEOUTS

    def __reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz

    def close(self):
        self.running = False
        self.socket.close()
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)

    def join(self):
        self.thread.join()


class Server_udp:
    def __init__(self, address, port, dir_addr, printer):
        self.address = address
        self.port = port
        self.socket = None
        self.active_connections = {}
        self.fmanager = FileManager(dir_addr)
        self.printer = printer
        self.running = False

        self.listener = None
        self.cleaner = None

    def run(self):
        self.running = True
        self.create_socket()
        self._setup_cleaner()
        self._setup_listener()
        self._read_input()

    def create_socket(self):
        self.socket = server_socket_udp(self.address, self.port)
        self.socket.bind()

    def listen(self):
        self.printer.print_listening_on((self.address, self.port))
        try:
            while self.running:
                package, address = self.socket.blocking_recv()
                self.demux(package, address)
        except ConnectionResetError:
            self.printer.print_connection_lost(self.address)

    def demux(self, package, address):

        if not package or not address:
            return

        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, addr):
        c = Connection_instance(addr, self.fmanager, self.printer)
        c.start()
        self.active_connections[addr] = c

    def _setup_listener(self):
        self.listener = Thread(target=self.listen)
        self.listener.start()

    def _setup_cleaner(self):
        self.cleaner = Thread(target=self._periodic_clean)
        self.cleaner.start()

    def _read_input(self):
        while self.running:
            read_from_stdin = input()
            if read_from_stdin == EXIT:
                self.running = False
        self.close()

    def _periodic_clean(self):
        while self.running:
            time.sleep(CONNECTION_TIMEOUT)
            abortpckg = AbortPackage()

            self.active_connections = {addr: c for addr, c
                                       in self.active_connections.items()
                                       if c.is_active() or c.push(abortpckg)
                                       or c.join()}

    def close(self):
        self.running = False
        for addr, connection in self.active_connections.items():
            connection.push(AbortPackage())
            connection.join()

        self.socket.close()

        if self.cleaner:
            self.cleaner.join()
        if self.listener:
            self.listener.join()
        self.printer.print_program_closed()
