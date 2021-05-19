import queue
import time
from threading import Thread

from lib.common import FileManager, CHUNK_SIZE
from lib.package import Package, Header
from lib.socket_udp import socket_udp
from lib.common import DOWNLOAD, UPLOAD, ABORT, CONNECTION_TIMEOUT, MAX_TIMEOUTS


class Connection_instance:
    def __init__(self, socket, address, fmanager):
        self.socket = socket
        self.address = address
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.__init_sequnums()
        self.running = False
        self.last_active = time()
        self.timeouts = 0

    def push(self, package):
        self.package_queue.put(package)
        self.last_active = time()

    def pull(self):
        package = self.package_queue.get()
        package.validate()
        return package

    def start(self):
        self.running = True
        thread = Thread(target=self.dispatch)
        thread.start()
        thread.join()

    # el timer de conexion de implementaria en este loop
    # se envia un abort package al client en el timer interrupt
    def dispatch(self):
            package = self.pull()
            ptype = package.header.req

            try:
                if ptype == DOWNLOAD:
                    ptype.do_download(package)
            except AbortedException:
                # close file or something idk

    # esta garantizado que el package es de tipo upload
    # notar que no importa si es el primer packete o si es uno del medio
    # siempre la operacion es la misma y es consistente
    def do_upload(self, package):
        self.current_seqnum = -1
        while True:  # either finished or gets aborted

            if package.seqnum == self.current_seqnum + 1:
                finished = self.__reconstruct_file(package)
                if finished:
                    self.__close()
                    self.fmanager.close(package.header.name)
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

    def is_active():
        timed_out = time.time() - self.last_active > CONNECTION_TIMEOUT
        self.timeouts = self.timeouts + 1 if timed_out else 0
        return self.timeouts <= MAX_TIMEOUTS

    def __close(self):
        self.running = False

    def __send(self, package):
        self.last_sent_package = package
        bytestream = Package.serialize(package)
        self.socket.send(bytestream, self.address)

    def __reconstruct_file(self, package):
        path = self.fmanager.absolute_path(package.header.name)
        written = self.fmanager.write(path, 'rb')
        return written >= package.header.filesz

    def __send_ack(self):
        ack = Package.create_ack(self.current_seqnum)
        bytestream = Package.serialize(ack)
        self.socket.send(bytestream, self.address)


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
            package = self.__get_new_package()
            self.demux(package)

    def __get_new_package(self):

        message, address = self.socket.recv(CHUNK_SIZE)
        package = Package.deserialize(message)
        return package

    def demux(self, package):
        address = package.get_src_address()

        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, address):
        conn = Connection_instance(self.socket, address, self.fmanager, self)
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
                                       if c.is_active() or c.push(abortpckg)}
