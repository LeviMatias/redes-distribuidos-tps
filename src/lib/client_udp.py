from lib.common import FileManager, CHUNK_SIZE
from lib.package import Package, Header
from lib.socket_udp import socket_udp
from lib.common import DOWNLOAD, UPLOAD, ABORT, NULL, CONNECTION_TIMEOUT
import time


class Client_udp:

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = None
        self.fmanager = FileManager()
        self.on = False
        self.last_active = time()

    def __init_sequnums(self):
        self.current_seqnum = -1
        self.expected_seqnum = self.current_seqnum + 1

    def __update_seqnums(self):
        self.current_seqnum += 1
        self.expected_seqnum = self.current_seqnum + 1

    def __get_next_seqnum(self, seqnum):
        return seqnum + 1

    def create_socket(self):
        self.socket = socket_udp(self.address, self.port)

    def listen(self):
        while not self.__timeout():
            package = self.__recv_package()
            self.__dispatch(package)

    def __timeout(self):
        return time.time() - self.timer < CONNECTION_TIMEOUT

    def __dispatch(self, package):
        ptype = package.get_type()
        if ptype == DOWNLOAD: 
            self.do_download(package)
        elif ptype == UPLOAD: # confuso porque no se lee que es un ACK TODO
            self.do_upload(package)
        elif ptype == ABORT:
            self.do_abort(package)
        elif ptype == NULL:  # medio confuso TODO
            pass
        else:
            self.do_recv_unidentified(package)

    def __recv_package(self):
        message, address = self.socket.recv(CHUNK_SIZE)

        if message:
            self.last_active = time()
        package = Package.deserealize(message, address)
        return package

    def upload(self, path):

        self.on = True
        send_package = self.__extract_next_package(-1, path)  # raro el -1 TODO
        self.__update_seqnums()
        self.__send(send_package)

        while self.on:
            self.listen()
            self.do_upload()

    def __extract_next_package(self, seqnum, path):
        next_seqnum = self.__get_next_seqnum(seqnum)  # raro TODO

        filesz = self.fmanager.get_size(path)
        header = Header(next_seqnum, DOWNLOAD, path, filesz)

        size = CHUNK_SIZE - header.size
        payload = self.fmanager.read_chunk(size, path, how='br')
        return Package(header, payload)

    def do_upload(self, package):
        ack_seqnum = package.get_seqnum()
        path = package.get_path()

        if ack_seqnum == self.current_seqnum:
            send_package = self.__extract_next_package(ack_seqnum, path)
            self.__update_seqnums()
            self.__send(send_package)
        else:
            self.__retransmit()

    def do_download(self, package):
        pass

    def do_abort(self, package):
        pass

    def do_recv_unidentified(self, package):
        pass
