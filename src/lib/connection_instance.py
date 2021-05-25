import time
import queue
from threading import Thread, Timer

from lib.file_manager import FileManager
from lib.package import Package, Header
from lib.socket_udp import CHUNK_SIZE
from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException

CONNECTION_TIMEOUT = 1000
MAX_TIMEOUTS = 3


class Connection_instance:
    def __init__(self, socket, dst_address, printer):
        self.socket = socket
        self.dst_address = dst_address
        
        self.printer = printer
        self.running = False

        self.timer = Timer(CONNECTION_TIMEOUT)
        
        self.fmanager = FileManager
        self.in_use_file_path = None

        self.recv_queue = queue.Queue()
        self.to_send_queue = queue.Queue()

    def push_to_recv(self, package):
        self.recv_queue.put(package)

    def pull_from_recv(self):
        package = self.recv_queue.get()
        return package

    def push_to_send(self, package):
        self.to_send_queue.put(package)

    def pull_from_send(self):
        package = self.to_send_queue.get()
        return package

    def has_to_send(self):
        return not self.to_send_queue.empty()

    def start(self):
        self.running = True
        self.connection_thread = Thread(target=self.dispatch)
        self.connection_thread.start()

    def dispatch(self):
        try:
            first = self.pull()
            ptype = first.header.req

            if ptype == UPLOAD:
                self.do_upload(first)
            elif ptype == DOWNLOAD:
                self.do_download(first)

        except AbortedException:
            self.close()

    def do_upload(self, firts_pckg):

        name = firts_pckg.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path

        last_recv_seqnum = -1
        package = firts_pckg
        transmition_complt = False
        while self.running and not transmition_complt:

            if package.header.seqnum == last_recv_seqnum + 1:
                finished = self.__reconstruct_file(package, path)
                last_recv_seqnum += 1
                self.socket.send_ack(last_recv_seqnum, self.address)

            if finished:
                self.fmanager.close_file(path)
                self.__close()
                transmition_complt = True
            else:
                package = self.pull()

    def do_download(self, request):

        name = request.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path
        filesz = self.fmanager.get_size(path)
        seqnum = request.header.seqnum
        bytes_sent = 0

        while self.running and bytes_sent < filesz:
            header = Header(seqnum, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            package = Package(header, payload)
            self.socket.reliable_send(package, self.address, self.pckg_queue)

            bytes_sent += len(payload)
            seqnum += 1

        self.fmanager.close_file(path)

    def __reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz

    def is_active(self):
        timed_out = time.time() - self.last_active > CONNECTION_TIMEOUT
        self.timeouts = self.timeouts + 1 if timed_out else 0
        return self.timeouts <= MAX_TIMEOUTS

    def close(self):
        self.running = False
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)

    def join(self):
        self.connection_thread.join()
