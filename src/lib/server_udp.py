import queue
import time
from threading import Thread

from lib.common import FileManager, CHUNK_SIZE, UPLOAD
from lib.package import Package, Header
from lib.socket_udp import socket_udp
from lib.common import DOWNLOAD, ABORT, CONNECTION_TIMEOUT, MAX_TIMEOUTS
from lib.common import AbortedException, TimeOutException


class Connection_instance:
    def __init__(self, socket, address, fmanager):
        self.socket = socket
        self.address = address
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.running = False
        self.last_active = time.time()
        self.timeouts = 0

    def push(self, package):
        self.package_queue.put(package)
        self.last_active = time.time()

    def pull(self):
        package = self.package_queue.get()
        return package

    def start(self):
        self.running = True
        self.thread = Thread(target=self.dispatch)
        self.thread.start()

    # el timer de conexion de implementaria en este loop
    # se envia un abort package al client en el timer interrupt
    def dispatch(self):
        package = self.pull()
        ptype = package.header.req

        try:
            if ptype == UPLOAD:
                self.do_upload(package)
            elif ptype == DOWNLOAD:
                self.do_download(package)
        except AbortedException:
            pass
            # close file or something idk

    # esta garantizado que el package es de tipo upload
    # notar que no importa si es el primer packete o si es uno del medio
    # siempre la operacion es la misma y es consistente
    def do_upload(self, package):
        self.current_seqnum = -1

        name = package.header.name
        server_file_path = self.fmanager.SERVER_BASE_PATH + name
        
        while self.running:  # either finished or gets aborted

            if package.header.seqnum == self.current_seqnum + 1:
                finished = self.__reconstruct_file(package, server_file_path)
                if finished:
                    self.__close()
                    self.fmanager.close(server_file_path)
                    return
                self.current_seqnum += 1

            package = self._get_next_package()

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

    def __send_ack(self):
        ack = Package.create_ack(self.current_seqnum)
        bytestream = Package.serialize(ack)
        self.socket.send(bytestream, self.address)

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
        self.socket = socket_udp(self.address, self.port)

    # socket.sendto(OK_ACK, package.src_address)
    def listen(self):
        while(True):
            package, address = self.__get_new_package()
            self.demux(package, address)

    def __get_new_package(self):

        message, address = self.socket.recv(CHUNK_SIZE)
        package = Package.deserialize(message)
        return package, address

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
            abortpckg = Package(Header(-1, ABORT, "", 0), "")

            self.active_connections = {addr: c for c, addr
                                       in self.active_connections.items()
                                       if c.is_active() or c.push(abortpckg)
                                       or c.join()}
