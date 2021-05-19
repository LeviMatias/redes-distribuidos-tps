import queue
import time
from threading import Thread

from lib.common import FileManager, CHUNK_SIZE
from lib.package import Package, Header
from lib.socket_udp import socket_udp
from lib.common import DOWNLOAD, UPLOAD, ABORT, CONNECTION_TIMEOUT, MAX_TIMEOUTS, TimeOutException, AbortedException


class Client_udp:
    def __init__(self, address, fmanager):
        self.socket = socket_udp(self.address, self.port)
        self.address = address
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.__init_sequnums()
        self.running = False
        self.last_active = time()
        self.timeouts = 0

    def do_upload(self):
        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz:
            header = Header(seqnum, DOWNLOAD, path, filesz)

            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='br')

            acked = False
            while not acked:
                try:
                    self.__send(Package(header, payload))
                    acked = self.__recv_ack().header.seqnum = seqnum
                    seqnum = seqnum + 1 if acked else seqnum
                except TimeOutException:
                    acked = False

        self.fmanager.close(path)

    def __send(self, package):
        self.last_sent_package = package
        bytestream = Package.serialize(package)
        self.socket.send(bytestream, self.address)

    def __recv_ack(self):
        return listen_for_next()

    def _active(self):
        timed_out = time.time() - self.last_active > CONNECTION_TIMEOUT

        if timed_out and self.timeouts < MAX_TIMEOUTS  # permissible timeout ocurred
            self.timeouts = self.timeouts + 1
            self.last_active = time.time() # reset
            raise TimeOutException()
        elif timed_out: # reached timeout limit, connection assumed lost
            raise AbortedException()

        return True

    def __send_ack(self):
        ack = Package.create_ack(self.current_seqnum)
        bytestream = Package.serialize(ack)
        self.socket.send(bytestream, self.address)

    def listen_for_next(self):
        package = None
        while not package and self._active():
            package = self.socket.recv(CHUNK_SIZE)

        self.last_active = time()
        self.timeouts = 0 # probably a better idea to implement the blocking queue
        return Package.deserealize(package)
