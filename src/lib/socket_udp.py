from socket import AF_INET, SOCK_DGRAM, socket
from lib.package import Package
from lib.common import CHUNK_SIZE, ACK, CONNECTION_TIMEOUT, MAX_TIMEOUTS
from lib.exceptions import TimeOutException, AbortedException
import time


class socket_udp:

    def __init__(self, address, port, always_open=False):
        self.address = address
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.last_active = time.time()
        self.timeouts = 0
        self.always_open = always_open

    def bind(self):
        self.socket.bind((self.address, self.port))

    def reliable_send(self, package):
        self.send(package)
        self.__recv_ack_to(package)  # waits until ack or triple timeouts

    def listen_for_next(self, last_recvd_seqnum):

        package_recvd = False
        while not package_recvd and self.__active():
            recv_bytestream, _ = self.socket.recvfrom(CHUNK_SIZE)

            if recv_bytestream:
                package = Package.deserialize(recv_bytestream)
                recvd_seqnum = package.header.seqnum
                package_recvd = recvd_seqnum == (last_recvd_seqnum + 1)

        return package

    def __recv_ack_to(self, package):
        try:
            ack_recvd = False
            while not ack_recvd and self.__active():
                recv_bytestream, _ = self.socket.recvfrom(CHUNK_SIZE)

                if recv_bytestream:
                    recvd_package = Package.deserialize(recv_bytestream)

                    if self.__is_correct_ack(recvd_package, package):
                        ack_recvd = True

            self.__reset_timer()
            self.__reset_timeouts()

        except TimeOutException:
            self.reliable_send(package)  # retransmit

    def send(self, package):
        bytestream = Package.serialize(package)
        self.socket.sendto(bytestream, self.address)

    def __is_correct_ack(self, recvd_package, last_sent_package):
        is_ack = recvd_package.header.req == ACK
        recv_seq = recvd_package.header.seqnum
        sent_seq = last_sent_package.header.seqnum
        is_expected_seqnum = recv_seq == sent_seq
        return is_ack and is_expected_seqnum

    def __reset_timer(self):
        self.last_active = time.time()

    def __reset_timeouts(self):
        self.timeouts = 0  # probably a better idea to implement the blocking q

    def __active(self):
        timed_out = (time.time() - self.last_active) > CONNECTION_TIMEOUT

        if timed_out and self.timeouts < MAX_TIMEOUTS:  # permissible timeout
            self.timeouts = self.timeouts + 1
            self.__reset_timer()
            raise TimeOutException()
        elif timed_out and not self.always_open:  # reached timeout limit
            raise AbortedException()  # connection assumed lost
        else:
            return True
