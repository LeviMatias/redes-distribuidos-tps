import queue
import time
from threading import Thread

from lib.file_manager import FileManager
from lib.package import Package, AbortPackage, Header
from lib.socket_udp import CONNECTION_TIMEOUT, MAX_TIMEOUTS, CHUNK_SIZE
from lib.socket_udp import socket_udp
from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException


class Connection_instance:
    def __init__(self, socket, address, fmanager, printer):
        self.socket = socket
        self.address = address
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.printer = printer
        self.running = False
        self.timeouts = 0
        self.in_use_file_path = None

    def push(self, package):
        self.package_queue.put(package)
        self.last_active = time.time()

    def pull(self):
        package = self.package_queue.get()
        package.validate()
        return package

    def start(self):
        self.running = True
        self.thread = Thread(target=self.dispatch)
        self.thread.start()

    def dispatch(self):
        try:
            first = self.pull()
            ptype = first.header.req

            if ptype == UPLOAD:
                self.do_upload(first)
            elif ptype == DOWNLOAD:
                self.do_download(first)

        except AbortedException:
            if self.in_use_file_path:
                self.fmanager.close_file(self.in_use_file_path)
            self.__close()

    def do_upload(self, firts_pckg):

        name = firts_pckg.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path

        last_recv_seqnum = -1
        package = firts_pckg
        transmition_complt = False
        while self.running and not transmition_complt:

            if package.header.seqnum == last_recv_seqnum + 1:
                finished = self.__reconstruct_file(package, path)
                last_recv_seqnum += 1
                self.socket.send_ack(last_recv_seqnum, self.address)

            if finished:
                self.fmanager.close_file(path)
                self.__close()
                transmition_complt = True
            else:
                package = self.pull()

    def do_download(self, request):

        ack = Package.create_ack(request.header.seqnum)

        name = request.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path
        filesz = self.fmanager.get_size(path)
        seqnum = request.header.seqnum
        bytes_sent = 0

        while self.running and bytes_sent < filesz:
            header = Header(seqnum, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)
            self.socket.reliable_send(package, self.address)

            bytes_sent += len(payload)
            seqnum += 1

        self.fmanager.close_file(path)

    def is_active(self):
        timed_out = time.time() - self.last_active > CONNECTION_TIMEOUT
        self.timeouts = self.timeouts + 1 if timed_out else 0
        return self.timeouts <= MAX_TIMEOUTS

    def __close(self):
        self.running = False

    def __reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz

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
        self.socket = socket_udp(self.address, self.port, always_open=True)
        self.socket.bind()

    def listen(self):
        while(True):
            package, address = self.socket.recv()
            self.demux(package, address)

    def demux(self, package, address):
        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, addr):
        c = Connection_instance(self.socket, addr, self.fmanager, self.printer)
        c.start()
        self.active_connections[addr] = c

    def _setup_cleaner(self):
        Thread(target=self._periodic_clean).start()

    def _periodic_clean(self):
        while True:
            time.sleep(CONNECTION_TIMEOUT)
            abortpckg = AbortPackage()

            self.active_connections = {addr: c for addr, c
                                       in self.active_connections.items()
                                       if c.is_active() or c.push(abortpckg)
                                       or c.join()}
