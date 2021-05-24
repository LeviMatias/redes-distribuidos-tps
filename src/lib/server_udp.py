import queue
import time
from threading import Thread

from lib.common import FileManager, CHUNK_SIZE, UPLOAD
from lib.package import Package, AbortPackage, Header
from lib.socket_udp import socket_udp
from lib.common import DOWNLOAD, CONNECTION_TIMEOUT, MAX_TIMEOUTS
from lib.exceptions import AbortedException, TimeOutException


class Connection_instance:
    def __init__(self, socket, address, fmanager):
        self.socket = socket
        self.address = address
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.running = False
        self.current_seqnum = 0

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
            self.__close()

    def do_upload(self, firts_pckg):

        name = firts_pckg.header.name
        server_file_path = self.fmanager.SERVER_BASE_PATH + name
        finished = False

        package = firts_pckg
        transmition_complt = False
        while self.running and not transmition_complt:

            if package.header.seqnum == self.current_seqnum + 1:
                finished = self.__reconstruct_file(package, server_file_path)
                self.current_seqnum += 1

            self.socket.send_ack(self.current_seqnum, self.address)
            if finished:
                self.fmanager.close_file(server_file_path)
                self.__close()
                transmition_complt = True
            else:
                package = self.pull()

    def do_download(self, firts_pckg):
        path = firts_pckg.header.path
        name = firts_pckg.header.name
        filesz = self.fmanager.get_size(path)
        seqnum = 0
        bytes_sent = 0

        while self.running and bytes_sent < filesz:
            header = Header(seqnum, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)
            self.socket.reliable_send(package, self.address)
            bytes_sent += len(payload)

        self.fmanager.close_file(path)

    def _get_next_package(self):
        package = None
        while not package:
            try:
                self.__send_ack()
                package = self.pull()
            except TimeOutException:
                package = None
        return package

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
    def __init__(self, address, port, dir_addr):
        self.address = address
        self.port = port
        self.active_connections = {}
        self.socket = None
        self.fmanager = FileManager(dir_addr)

    def run(self):
        self.create_socket()
        self._setup_cleaner()
        self.listen()

    def create_socket(self):
        self.socket = socket_udp(self.address, self.port, always_open=True)

    def listen(self):
        while(True):
            package, address = self.__get_new_package()
            self.demux(package, address)

    def demux(self, package, address):
        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, address):
        conn = Connection_instance(self.socket, address, self.fmanager)
        conn.start()
        self.active_connections[address] = conn

    def _setup_cleaner(self):
        Thread(target=self._periodic_clean)

    def _periodic_clean(self):
        while True:
            time.sleep(CONNECTION_TIMEOUT)
            abortpckg = AbortPackage()

            self.active_connections = {addr: c for c, addr
                                       in self.active_connections.items()
                                       if c.is_active() or c.push(abortpckg)
                                       or c.join()}
