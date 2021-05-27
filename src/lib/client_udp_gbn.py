from threading import Thread
from lib.client_udp import Client_udp
from lib.socket_udp import CHUNK_SIZE, CONNECTION_TIMEOUT
from lib.package import Package, Header, UPLOAD
from lib.timer import Timer

W_SIZE = 5


class Client_udp_gbn(Client_udp):

    def __init__(self, address, port, fmanager, printer):
        super().__init__(address, port, fmanager, printer)
        
        self.running = True
        self.file_finished = False

        self.window_base = 0
        self.last_sent_seqnum = -1
        self.seqnum_head = 0
        self.sendq = []

    def window_full(self):
        return (self.seqnum_head - self.window_base) == W_SIZE

    def fill_sending_queue(self, path, name):

        filesz = self.fmanager.get_size(path)
        while not self.window_full() and not self.file_finished:
            header = Header(self.seqnum_head, UPLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')
            if (len(payload) == 0):
                self.file_finished = True
            pkg = Package(header, payload)
            self.sendq.append(pkg)
            self.seqnum_head += 1

    def send_queued_unsent(self):
        amount_sent = self.seqnum_head - (self.last_sent_seqnum + 1)
        for i in range(self.last_sent_seqnum + 1, self.seqnum_head):
            pkg = self.sendq[i]
            self.socket.send(pkg, self.address)

        self.last_sent_seqnum += amount_sent

    def recv_acks(self):
        while not self.file_finished and self.running:
            pkg, _ = self.socket.blocking_recv()
            if pkg.is_ack():
                ack_seqnum = pkg.header.seqnum
                self.window_base = ack_seqnum
                self.sendq = self.sendq[self.window_base:]

    def send_all_queued(self):
        for pkg in self.sendq:
            self.socket.send(pkg, self.address)

    def do_upload(self, path, name):

        acks_listener = Thread(target=self.recv_acks)
        acks_listener.start()

        timer = Timer(CONNECTION_TIMEOUT)
        timer.start()
        try:
            while not self.file_finished and self.running:
                try:
                    self.fill_sending_queue(path, name)
                    self.send_queued_unsent()
                except TimeoutError:
                    timer.reset()
                    self.send_all_queued()
                    continue
            timer.stop()
        except KeyboardInterrupt:
            timer.stop()

        self.running = False
        self.fmanager.close_file(path)
        acks_listener.join()
