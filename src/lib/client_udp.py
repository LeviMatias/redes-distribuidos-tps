from lib.file_manager import FileManager
from lib.package import Package, Header, UPLOAD
from lib.exceptions import AbortedException
from lib.socket_udp import client_socket_udp, CHUNK_SIZE


class Client_udp:
    def __init__(self, address, port, printer):

        self.socket = client_socket_udp(address, port)
        self.address = (address, port)
        self.fmanager = FileManager()
        self.printer = printer

        self.in_use_file_path = None

    def upload(self, path, name):
        self._data_transfer(path, name, self.do_upload)

    def download(self, path, name):
        self._data_transfer(path, name, self.do_download)

    def _data_transfer(self, path, name, protocol):
        self.in_use_file_path = path
        try:
            protocol(path, name)
        except (AbortedException, KeyboardInterrupt):
            self.close()

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
        last_recv_seqnum = -1

        req_pkg = Package.create_download_request(name)
        first_packg = self.socket.reliable_send_and_recv(req_pkg, self.address)
        last_recv_seqnum += 1
        transmition_complt = self.__reconstruct_file(first_packg, path)

        if transmition_complt:
            self.fmanager.close_file(path)

        self.socket.send_ack(last_recv_seqnum, self.address)

        while not transmition_complt:

            package = self.socket.listen_for_next_from(last_recv_seqnum)
            last_recv_seqnum += 1

            transmition_complt = self.__reconstruct_file(package, path)
            
            if transmition_complt:
                self.fmanager.close_file(path)

            self.socket.send_ack(last_recv_seqnum, self.address)

    def __reconstruct_file(self, package, path):
        written = self.fmanager.write(path, package.payload, 'wb')
        return written >= package.header.filesz

    def close(self):
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)
        print("CONNECTION LOST")
