from threading import Thread
from math import ceil

from lib.client_udp import Client_udp
from lib.socket_udp import CHUNK_SIZE, CONNECTION_TIMEOUT
from lib.package import Package, Header, UPLOAD
from lib.timer import Timer
from lib.exceptions import TimeOutException

W_SIZE = 200


class Client_udp_gbn(Client_udp):

    def __init__(self, address, port, fmanager, printer):
        super().__init__(address, port, fmanager, printer)

        self.window_base = 0
        self.last_sent_seqnum = -1
        self.seqnum_head = 0
        self.sendq = []

    def window_full(self):
        return (self.seqnum_head - self.window_base) == W_SIZE

    def fill_sending_queue(self, path, name):

        filesz = self.fmanager.get_size(path)
        file_finished = False
        while not self.window_full() and not file_finished:
            header = Header(self.seqnum_head, UPLOAD, path, name, filesz)
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
        while self.running:
            pkg, _ = self.socket.blocking_recv()

            if not pkg:
                break
                # el blocking_recv devuelve None si el socket cierra

            if pkg.is_ack():
                ack_seqnum = pkg.header.seqnum
                self.window_base = ack_seqnum
                timer.reset()

    def send_all_queued(self):
        unkacked = self.sendq[self.window_base: self.seqnum_head]
        for pkg in unkacked:
            self.socket.send(pkg, self.address)

    def do_upload(self, path, name):

        print('GBN upload')
        fsize = self.fmanager.get_size(path)
        end_seqnum = ceil(fsize/CHUNK_SIZE)

        timer = Timer(CONNECTION_TIMEOUT)
        acks_listener = Thread(args=[timer], target=self.recv_acks)
        acks_listener.start()

        timer.start()
        transfer_complt = False
        try:
            while not transfer_complt and self.running:
                try:
                    timer.update()
                    self.fill_sending_queue(path, name)
                    self.send_queued_unsent()

                    if self.window_base == (end_seqnum - 1):
                        transfer_complt = True

                    b_arrived = self.last_sent_seqnum * CHUNK_SIZE
                    self.printer.progressBar(b_arrived, fsize)
                except TimeOutException:
                    timer.reset()
                    self.send_all_queued()
            timer.stop()
        except (KeyboardInterrupt, ConnectionResetError):
            timer.stop()

        b_arrived = self.last_sent_seqnum * CHUNK_SIZE
        self.printer.progressBar(b_arrived, fsize)
        self.printer.print_upload_finished(name)

        self.close()
        self.fmanager.close_file(path)
        acks_listener.join()
