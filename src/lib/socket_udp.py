from socket import AF_INET, SOCK_DGRAM, socket
from lib.package import Package, ACK
from lib.exceptions import TimeOutException, AbortedException
import time
import abc
# import random

CHUNK_SIZE = 1024*20

CONNECTION_TIMEOUT = 0.05
MAX_TIMEOUTS = 20


class socket_udp (metaclass=abc.ABCMeta):

    def __init__(self, address, port):
        # connection attr
        self.address = address
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.running = True

        # socket mode
        self.always_open = False
        self.socket.setblocking(False)

        # time management
        self.begin_time = time.time()
        self.last_active = time.time()
        self.timeouts = 0
        self.always_open = False
        self.timeout_limit = CONNECTION_TIMEOUT

        # stats
        self.t_bytes_sent = 0
        self.t_bytes_sent_ok = 0
        self.t_bytes_recv = 0
        self.acks_recv = 0
        self.pkg_sent = 0
        self.pkg_recvd = 0
        self.t_timeouts = 0

    def _recv(self):
        try:
            return self.socket.recvfrom(CHUNK_SIZE)
        except (BlockingIOError, OSError):
            return None, None

    def reliable_send(self, package, address, package_queue=None):
        for i in range(MAX_TIMEOUTS + 1):
            try:
                self.send(package, address)
                self._recv_ack_to(package, package_queue)
                self.t_bytes_sent_ok += len(package.payload)
            except TimeOutException:
                continue

    def reliable_send_and_recv(self, package, address, package_queue=None):
        pass

    def listen_for_next_from(self, last_recvd_seqnum, package_queue=None):
        pass

    def recv_with_timer(self, package_queue=None):
        pass

    @abc.abstractmethod
    def _recv_ack_to(self, package, package_queue=None):
        pass

    def blocking_recv(self, timer=None):

        package = None
        address = None
        package_recvd = False
        while not package_recvd and self.running:

            if timer:
                timer.update()

            recv_bytestream, address = self._recv()

            if recv_bytestream:
                package = Package.deserialize(recv_bytestream)
                package_recvd = True

        self.update_recv_stats(package)
        return package, address

    def send(self, package, address):
        bytestream = Package.serialize(package)
        sz = len(bytestream)
        self.t_bytes_sent += sz
        self.pkg_sent += 1

        # if random.randint(0, 100) < 20:
        #    print("dropping " + str(package.header.seqnum))
        #    return 0
        try:
            self.socket.sendto(bytestream, address)
        except BlockingIOError:
            return 0
        return sz

    def send_ack(self, seqnum, address):
        ack = Package.create_ack(seqnum)
        self.send(ack, address)

    def update_recv_stats(self, pkg):
        if pkg:
            if pkg.is_ack():
                self.acks_recv += 1
            self.pkg_recvd += 1
            self.t_bytes_recv += len(pkg.payload)

    def _is_correct_ack(self, recvd_package, last_sent_package):
        is_ack = recvd_package.header.req == ACK

        recv_seq = recvd_package.header.seqnum
        sent_seq = last_sent_package.header.seqnum
        is_expected_seqnum = recv_seq == sent_seq

        return is_ack and is_expected_seqnum

    def _reset_timer(self):
        self.last_active = time.time()

    def _reset_timeouts(self):
        self.timeouts = 0  # probably a better idea to implement the blocking q

    def _active(self):
        timed_out = (time.time() - self.last_active) > self.timeout_limit

        if timed_out and self.timeouts < MAX_TIMEOUTS:  # permissible timeout
            self.timeouts = self.timeouts + 1
            self._reset_timer()
            self.t_timeouts += 1
            raise TimeOutException()
        elif timed_out and not self.always_open:  # reached timeout limit
            raise AbortedException()  # connection assumed lost

        return True

    def close(self):
        self.running = False
        self.socket.close()


class client_socket_udp (socket_udp):

    def __init__(self, address, port):
        super().__init__(address, port)
        self.timeout_limit = CONNECTION_TIMEOUT
        self.client = True

    def reliable_send_and_recv(self, package, address, package_queue=None):
        recv_package = None
        while not recv_package:
            try:
                sent = self.send(package, address)
                recv_package, _ = self.recv_with_timer(package_queue)
                self.t_bytes_sent_ok += sent
                return recv_package
            except TimeOutException:
                pass

    def listen_for_next_from(self, last_recvd_seqnum, package_queue=None):

        package_recvd = False
        while not package_recvd:
            try:
                self._active()
                recv_bytestream, _ = self._recv()

                if recv_bytestream:
                    package = Package.deserialize(recv_bytestream)
                    recvd_seqnum = package.header.seqnum
                    package_recvd = recvd_seqnum == (last_recvd_seqnum + 1)
            except TimeOutException:
                self.send_ack(last_recvd_seqnum, (self.address, self.port))

        self.update_recv_stats(package)
        self._reset_timer()
        self._reset_timeouts()
        return package

    def recv_with_timer(self, package_queue=None):

        package_recvd = False
        while not package_recvd and self._active():
            recv_bytestream, address = self._recv()

            if recv_bytestream:
                package = Package.deserialize(recv_bytestream)
                package_recvd = True

        self.update_recv_stats(package)
        self._reset_timer()
        self._reset_timeouts()
        return package, address

    def _recv_ack_to(self, package, package_queue=None):

        ack_recvd = False
        while not ack_recvd and self._active():
            recv_bytestream, _ = self._recv()

            if recv_bytestream:
                recvd_package = Package.deserialize(recv_bytestream)

                if self._is_correct_ack(recvd_package, package):
                    ack_recvd = True

        self.update_recv_stats(recvd_package)
        self._reset_timer()
        self._reset_timeouts()


class server_socket_udp (socket_udp):

    def __init__(self, address, port):
        super().__init__(address, port)
        self.always_open = True
        self.server = True
        self.timeout_limit = CONNECTION_TIMEOUT

    def bind(self):
        self.socket.bind((self.address, self.port))

    def blocking_recv_through(self, package_queue=None, timer=None):

        recvd_package = None
        while not recvd_package and self.running:

            if timer:
                timer.update()

            if not package_queue.empty():
                recvd_package = package_queue.get()
                recvd_package.validate()

        self.update_recv_stats(recvd_package)
        return recvd_package

    def _recv_ack_to(self, package, package_queue=None):
        ack_recvd = False
        while not ack_recvd and self._active():

            if not package_queue.empty():
                recvd_package = package_queue.get()
                recvd_package.validate()

                if self._is_correct_ack(recvd_package, package):
                    ack_recvd = True

        self.update_recv_stats(recvd_package)
        self._reset_timer()
        self._reset_timeouts()
