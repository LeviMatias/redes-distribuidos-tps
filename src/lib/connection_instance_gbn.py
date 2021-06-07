from threading import Thread
from lib.connection_instance import Connection_instance
from lib.timer import Timer
from lib.exceptions import TimeOutException, GBNTimeOut
from lib.common import W_SIZE, GBN_TIMEOUT
from lib.package import Package, Header
from lib.package import DOWNLOAD
from lib.exceptions import AbortedException, ConnectionInterrupt
from lib.socket_udp import MAX_TIMEOUTS, CONNECTION_TIMEOUT
from lib.socket_udp import CHUNK_SIZE


class Connection_instance_gbn(Connection_instance):

    def __init__(self, address, fmanager, printer):
        super().__init__(address, fmanager, printer)

        self.window_base = 0
        self.last_sent_seqnum = -1
        self.seqnum_head = 0
        self.sendq = []
        self.b_sent = 0
        self.file_finished = False
        self.acks_listener = None

    def window_full(self):
        return (self.seqnum_head - self.window_base) >= W_SIZE

    def fill_sending_queue(self, path, name, filesz):

        while not self.window_full() and not self.file_finished:
            header = Header(self.seqnum_head, DOWNLOAD, path, name, filesz)
            size = CHUNK_SIZE - header.size
            payload = self.fmanager.read_chunk(size, path, how='rb')

            if (len(payload) == 0):
                self.file_finished = True
            else:
                pkg = Package(header, payload)
                self.sendq.append(pkg)
                self.seqnum_head += 1

        return self.file_finished

    def send_queued_unsent(self):
        amount_sent = 0
        unsent = self.sendq[self.last_sent_seqnum + 1: self.seqnum_head]
        for pkg in unsent:
            self.socket.send(pkg, self.address)
            self.b_sent += len(pkg.payload)
            amount_sent += 1
            self.logger.log(str(pkg.header.seqnum))

        self.last_sent_seqnum += amount_sent

    def recv_acks(self, timers):
        try:
            while self.running:
                pkg = self.socket.blocking_recv_through(self.pckg_queue)

                if not pkg:
                    break

                if pkg.is_ack() and pkg.header.seqnum > -1:
                    ack_seqnum = pkg.header.seqnum
                    self.update_sent_acked_stats(ack_seqnum)
                    self.socket.update_recv_stats(pkg)
                    self.window_base = ack_seqnum
                    [timer.reset() for timer in timers]
                    self.logger.log("ack" + str(ack_seqnum))
        except (AbortedException, ConnectionInterrupt):
            self.running = False

    def update_sent_acked_stats(self, ack_seqnum_recvd):

        pkgs_acked = self.sendq[self.window_base: ack_seqnum_recvd]

        for pkg_acked in pkgs_acked:
            self.socket.t_bytes_sent_ok += len(pkg_acked.payload)

    def send_all_queued(self):
        unkacked = self.sendq[self.window_base: self.seqnum_head]
        for pkg in unkacked:
            self.socket.send(pkg, self.address)
            self.logger.log(str(pkg.header.seqnum))

    def do_download(self, request, path, name):

        self.printer._print('GBN download')

        fsize = self.fmanager.get_size(path)

        gbn_timer = Timer(GBN_TIMEOUT, GBNTimeOut)
        connection_timer = Timer(CONNECTION_TIMEOUT, TimeOutException)
        timers = [gbn_timer, connection_timer]

        self.acks_listener = Thread(args=[timers],
                                    target=self.recv_acks)
        self.acks_listener.start()

        timeouts = 0
        [timer.start() for timer in timers]
        transfer_cmplt = False
        while not transfer_cmplt and self.running:
            try:
                [timer.update() for timer in timers]
                self.fill_sending_queue(path, name, fsize)
                self.send_queued_unsent()

                self.printer.print_progress(self.socket, self.b_sent, fsize)

                all_acked = self.window_base == self.last_sent_seqnum
                if self.file_finished and all_acked:
                    transfer_cmplt = True

            except GBNTimeOut:
                gbn_timer.reset()
                self.send_all_queued()

            except TimeOutException:
                timeouts += 1
                if timeouts >= MAX_TIMEOUTS:
                    raise(AbortedException)
                else:
                    connection_timer.reset()

        [timer.stop() for timer in timers]

        self.printer.print_progress(self.socket, self.b_sent, fsize)
        self.printer.print_download_finished(name)

    def close(self):
        super(Connection_instance_gbn, self).close()
        if self.acks_listener:
            self.acks_listener.join()
