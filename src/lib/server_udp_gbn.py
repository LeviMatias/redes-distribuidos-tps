from math import ceil
from threading import Thread


from lib.connection_instance import Connection_instance
from lib.timer import Timer
from lib.exceptions import TimeOutException
from lib.client_udp_gbn import W_SIZE
from lib.package import Package, Header
from lib.package import DOWNLOAD
from lib.exceptions import AbortedException
from lib.socket_udp import CONNECTION_TIMEOUT

from lib.socket_udp import CHUNK_SIZE


class Server_udp_gbn(Connection_instance):

    def __init__(self, address, port, fmanager, printer):
        super().__init__(address, port, fmanager, printer)

        self.window_base = 0
        self.last_sent_seqnum = -1
        self.seqnum_head = 0
        self.sendq = []

    def window_full(self):
        return (self.seqnum_head - self.window_base) == W_SIZE

    def fill_sending_queue(self, path, name, filesz):

        file_finished = False
        while not self.window_full() and not file_finished:
            header = Header(self.seqnum_head, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')

            if (len(payload) == 0):
                file_finished = True
            else:
                pkg = Package(header, payload)
                self.sendq.append(pkg)
                self.seqnum_head += 1

    def send_queued_unsent(self):
        amount_sent = 0
        unsent = self.sendq[self.last_sent_seqnum + 1: self.seqnum_head]
        for pkg in unsent:
            self.socket.send(pkg, self.address)
            amount_sent += 1

        self.last_sent_seqnum += amount_sent

    def recv_acks(self, timer):
        try:
            while self.running:
                pkg = self.socket.blocking_recv_through(self.pckg_queue)
                if pkg.is_ack():
                    ack_seqnum = pkg.header.seqnum
                    self.window_base = ack_seqnum
                    timer.reset()
        except AbortedException:
            pass

    def send_all_queued(self):
        unkacked = self.sendq[self.window_base: self.seqnum_head]
        for pkg in unkacked:
            self.socket.send(pkg, self.address)

    def do_download(self, request):

        print('GBN download')
        name = request.header.name
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path
        filesz = self.fmanager.get_size(path)
        end_seqnum = ceil(filesz/CHUNK_SIZE)

        try:
            timer = Timer(CONNECTION_TIMEOUT)
            acks_listener = Thread(args=[timer], target=self.recv_acks)
            acks_listener.start()

            timer.start()
            transfer_complt = False
            while not transfer_complt and self.running:
                try:
                    timer.update()
                    self.fill_sending_queue(path, name, filesz)
                    self.send_queued_unsent()

                    if self.window_base == (end_seqnum - 1):
                        transfer_complt = True

                    b_arrived = self.last_sent_seqnum * CHUNK_SIZE
                    self.printer.progressBar(b_arrived, filesz)
                except TimeOutException:
                    timer.reset()
                    self.send_all_queued()
            timer.stop()
        except (KeyboardInterrupt, ConnectionResetError, AbortedException):
            timer.stop()

        print(self.window_base)
        b_arrived = self.last_sent_seqnum * CHUNK_SIZE
        self.printer.progressBar(b_arrived, filesz)
        self.printer.print_download_finished(name)

        self.close()
        acks_listener.join()
        self.fmanager.close_file(path)
