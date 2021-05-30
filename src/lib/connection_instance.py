import queue
import time
from threading import Thread


from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException
from lib.package import Package, Header
from lib.socket_udp import CHUNK_SIZE


class Connection_instance:
    def __init__(self, socket, address, fmanager, printer):
        self.socket = socket
        self.address = address
        self.fmanager = fmanager
        self.printer = printer
        self.running = False
        self.in_use_file_path = None
        self.pckg_queue = queue.Queue()

    def push(self, package):
        self.pckg_queue.put(package)
        self.last_active = time.time()

    def pull(self):
        package = self.pckg_queue.get()
        return package

    def start(self):
        self.running = True
        self.thread = Thread(target=self.dispatch)
        self.thread.start()

    def dispatch(self):
        start = time.time()
        self.printer.print_connection_established(self.address)
        try:
            first = self.pull()
            ptype = first.header.req

            self.printer.print_begin_transfer(first.header.name)
            if ptype == UPLOAD:
                self.do_upload(first)
            elif ptype == DOWNLOAD:
                self.do_download(first)

        except AbortedException:
            if self.in_use_file_path:
                self.fmanager.close_file(self.in_use_file_path)
            self.printer.print_connection_lost(self.address)

        self.printer.print_connection_finished(self.address)
        self.printer.print_duration(time.time() - start)

    def do_upload(self, firts_pckg):

        print('GBN and S&W upload')
        name = firts_pckg.header.name
        size = firts_pckg.header.filesz
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path

        last_recv_seqnum = -1
        package = firts_pckg
        transmition_complt = False
        while self.running and not transmition_complt:

            if package.header.seqnum == last_recv_seqnum + 1:
                finished, written = self.__reconstruct_file(package, path)
                self.printer.progressBar(written, size)
                last_recv_seqnum += 1

            self.socket.send_ack(last_recv_seqnum, self.address)

            if finished:
                self.fmanager.close_file(path)
                self.__close()
                transmition_complt = True
            else:
                package = self.pull()
        self.printer.print_upload_finished(name)

    def do_download(self, request):

        print('S&W download')
        name = request.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path
        filesz = self.fmanager.get_size(path)
        seqnum = request.header.seqnum
        bytes_sent = 0

        while bytes_sent < filesz:
            header = Header(seqnum, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)
            self.socket.reliable_send(package, self.address, self.pckg_queue)

            bytes_sent += len(payload)
            seqnum += 1
        self.fmanager.close_file(path)
        self.printer.print_download_finished(name)

    def is_active(self):
        return self.running

    def close(self):
        self.running = False

    def __reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def join(self):
        self.thread.join()
