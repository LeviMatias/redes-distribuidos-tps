from lib.package import Package, Header, UPLOAD
from lib.exceptions import AbortedException
from lib.socket_udp import socket_udp, CHUNK_SIZE


class Client_udp:
    def __init__(self, address, port, fmanager, printer):

        self.socket = socket_udp(address, port)
        self.address = (address, port)
        self.fmanager = fmanager
        self.printer = printer

    def upload(self, path, name):
        self._data_transfer(path, name, self.do_upload)

    def download(self, path, name):
        self._data_transfer(path, name, self.do_download)

    def _data_transfer(self, path, name, protocol):
        try:
            protocol(path, name)
        except AbortedException:
            self.fmanager.close_file(path)
            print("CONNECTION LOST")

    def do_upload(self, path, name):

        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        while sent < filesz:
            header = Header(seqnum, UPLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)

            self.socket.reliable_send(package, self.address)

            sent += len(payload)
            seqnum += 1

        self.fmanager.close_file(path)

    def do_download(self, path, name):

        rquest_package = Package.create_download_request(name)
        #send

        last_recv_seqnum = -1
        transmition_complt = False
        while not transmition_complt:

            package = self.socket.listen_for_next_from(last_recv_seqnum)
            transmition_complt = self.__reconstruct_file(package, path)

            if transmition_complt:
                self.fmanager.close_file(path)

            last_recv_seqnum += 1

            self.socket.send_ack(last_recv_seqnum, self.address)

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz
