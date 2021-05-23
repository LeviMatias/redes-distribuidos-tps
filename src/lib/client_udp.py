from lib.common import CHUNK_SIZE, DOWNLOAD, UPLOAD
from lib.package import Package, Header
from lib.exceptions import AbortedException
from lib.socket_udp import socket_udp


class Client_udp:
    def __init__(self, address, port, fmanager, _printer):

        self.socket = socket_udp(address, port)
        self.address = (address, port)
        self.fmanager = fmanager
        self.running = False
        self.BASE_CLIENT_PATH = '.\\'

    def upload(self, path, name):
        self._data_transfer(path, name, self.do_upload, UPLOAD)

    def download(self, path, name):
        self._data_transfer(path, name, self.do_download, DOWNLOAD)

    def _data_transfer(self, path, name, protocol, protocol_type):
        try:
            self.handshake(protocol_type)
            protocol(path, name)
        except AbortedException:
            print("CONNECTION LOST")

    def handshake(self, protocol_type):
        request_package = Package.create_hello_package(protocol_type)
        self.socket.reliable_send(request_package)

    def do_upload(self, path, name):

        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz:
            header = Header(seqnum, UPLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)

            self.socket.reliable_send(package)

            sent += len(payload)
            seqnum += 1

        self.fmanager.close(path)

    def do_download(self, path, name):

        client_path = self.BASE_CLIENT_PATH + name
        seqnum = -1
        transmition_complt = False
        while self.running and not transmition_complt:

            package = self.socket.listen_for_next(seqnum)
            transmition_complt = self.__reconstruct_file(package, client_path)

            if transmition_complt:
                self.fmanager.close(path)
                self.__close()

            seqnum += 1

            self.__send_ack(seqnum)

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz

    def __close(self):
        self.running = False

    def __send_ack(self, current_seqnum):
        ack = Package.create_ack(current_seqnum)
        bytestream = Package.serialize(ack)
        self.socket.send(bytestream, self.address)
