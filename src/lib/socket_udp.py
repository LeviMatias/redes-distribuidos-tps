from socket import AF_INET, SOCK_DGRAM, socket
from lib.package import Package, ACK
from lib.exceptions import TimeOutException, AbortedException
import time
import abc

CHUNK_SIZE = 1024
PAYLOAD_SIZE = 1024

CONNECTION_TIMEOUT = 1000
MAX_TIMEOUTS = 3


class socket_udp (metaclass=abc.ABCMeta):

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.last_active = time.time()
        self.timeouts = 0
        self.always_open = False
        self.t_bytes_sent = 0
        self.t_bytes_sent_ok = 0
        self.t_bytes_recv = 0

    def reliable_send(self, package, address, package_queue=None):
        sent = self.send(package, address)
        try:
            self._recv_ack_to(package, package_queue)
            self.t_bytes_sent_ok += sent
        except TimeOutException:
            self.reliable_send(package, address, package_queue)

    def reliable_send_and_recv(self, package, address, package_queue=None):
        recv_package = None
        sent = self.send(package, address)
        try:
            recv_package, _ = self.recv_with_timer(package_queue)
            self.t_bytes_sent_ok += sent
            return recv_package
        except TimeOutException:
            self.reliable_send_and_recv(package, address, package_queue)

    @abc.abstractmethod
    def listen_for_next_from(self, last_recvd_seqnum, package_queue=None):
        pass

    @abc.abstractmethod
    def recv_with_timer(self, package_queue=None):
        pass

    @abc.abstractmethod
    def _recv_ack_to(self, package, package_queue=None):
        pass

    def blocking_recv(self):

        package_recvd = False
        while not package_recvd:
            recv_bytestream, address = self.socket.recvfrom(CHUNK_SIZE)
            self.t_bytes_recv += len(recv_bytestream)

            if recv_bytestream:
                package = Package.deserialize(recv_bytestream)
                package_recvd = True

        return package, address

    def send(self, package, address):
        bytestream = Package.serialize(package)
        self.socket.sendto(bytestream, address)
        sz = len(bytestream)
        self.t_bytes_sent += sz
        return sz

    def send_ack(self, seqnum, address):
        ack = Package.create_ack(seqnum)
        sent = self.send(ack, address)
        self.t_bytes_sent_ok += sent

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
        timed_out = (time.time() - self.last_active) > CONNECTION_TIMEOUT

        if timed_out and self.timeouts < MAX_TIMEOUTS:  # permissible timeout
            self.timeouts = self.timeouts + 1
            self._reset_timer()
            raise TimeOutException()
        elif timed_out and not self.always_open:  # reached timeout limit
            raise AbortedException()  # connection assumed lost
        else:
            return True


class client_socket_udp (socket_udp):

    def __init__(self, address, port):
        super().__init__(address, port)

    def listen_for_next_from(self, last_recvd_seqnum, package_queue=None):

        package_recvd = False
        while not package_recvd and self._active():
            recv_bytestream, _ = self.socket.recvfrom(CHUNK_SIZE)
            self.t_bytes_recv += len(recv_bytestream)

            if recv_bytestream:
                package = Package.deserialize(recv_bytestream)
                recvd_seqnum = package.header.seqnum
                package_recvd = recvd_seqnum == (last_recvd_seqnum + 1)

        return package

    def recv_with_timer(self, package_queue=None):

        package_recvd = False
        while not package_recvd and self._active():
            recv_bytestream, address = self.socket.recvfrom(CHUNK_SIZE)
            self.t_bytes_recv += len(recv_bytestream)

            if recv_bytestream:
                package = Package.deserialize(recv_bytestream)
                package_recvd = True

        return package, address

    def _recv_ack_to(self, package, package_queue=None):

        ack_recvd = False
        while not ack_recvd and self._active():
            recv_bytestream, _ = self.socket.recvfrom(CHUNK_SIZE)
            self.t_bytes_recv += len(recv_bytestream)

            if recv_bytestream:
                recvd_package = Package.deserialize(recv_bytestream)

                if self._is_correct_ack(recvd_package, package):
                    ack_recvd = True

        self._reset_timer()
        self._reset_timeouts()


class server_socket_udp (socket_udp):

    def __init__(self, address, port):
        super().__init__(address, port)
        self.always_open = True

    def bind(self):
        self.socket.bind((self.address, self.port))

    def listen_for_next_from(self, last_recvd_seqnum, package_queue=None):

        recv = False
        while not recv and self._active():

            if not package_queue.empty():
                recvd_package = package_queue.get()
                recvd_seqnum = recvd_package.header.seqnum
                recv = recvd_seqnum == (last_recvd_seqnum + 1)

        return recvd_package

    def recv_with_timer(self, package_queue=None):

        recvd_package = None
        while not recvd_package and self._active():

            if not package_queue.empty():
                recvd_package = package_queue.get()

        return recvd_package

    def _recv_ack_to(self, package, package_queue=None):
        ack_recvd = False
        while not ack_recvd and self._active():

            if not package_queue.empty():
                recvd_package = package_queue.get()

                if self._is_correct_ack(recvd_package, package):
                    ack_recvd = True

        self._reset_timer()
        self._reset_timeouts()
