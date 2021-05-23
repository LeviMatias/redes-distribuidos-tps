import queue
import time
from socket import AF_INET, SOCK_DGRAM, socket

from lib.common import CHUNK_SIZE, UPLOAD
from lib.package import Package, Header
from lib.common import TimeOutException, AbortedException
from lib.common import CONNECTION_TIMEOUT, MAX_TIMEOUTS


class Client_udp:
    def __init__(self, address, port, fmanager, _printer):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.address = (address, port)
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.running = False
        self.last_active = time.time()
        self.timeouts = 0

    def do_upload(self, path, name):
        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz:
            header = Header(seqnum, UPLOAD, path, name, filesz)

            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')

            acked = False
            while not acked:
                try:
                    self.__send(Package(header, payload))
                    acked = self.__recv_ack().header.seqnum == seqnum
                    seqnum = seqnum + 1 if acked else seqnum
                except TimeOutException:
                    acked = False

            sent += len(payload)

        self.fmanager.close(path)

    def __send(self, package):
        self.last_sent_package = package
        bytestream = Package.serialize(package)
        self.socket.sendto(bytestream, self.address)
        
    def __recv_ack(self):
        return self.listen_for_next()

    def _active(self):
        timed_out = (time.time() - self.last_active) > CONNECTION_TIMEOUT

        if timed_out and self.timeouts < MAX_TIMEOUTS:  # permissible timeout
            self.timeouts = self.timeouts + 1
            self.last_active = time.time()  # reset
            raise TimeOutException()
        elif timed_out:  # reached timeout limit, connection assumed lost
            raise AbortedException()

        return True

    def __send_ack(self):
        ack = Package.create_ack(self.current_seqnum)
        bytestream = Package.serialize(ack)
        self.socket.send(bytestream, self.address)

    def listen_for_next(self):
        package = None
        while not package and self._active():
            package, _addr = self.socket.recvfrom(CHUNK_SIZE)

        self.last_active = time.time()
        self.timeouts = 0  # probably a better idea to implement the blocking q
        return Package.deserialize(package)
