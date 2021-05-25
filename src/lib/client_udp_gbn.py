from lib.client_udp import Client_udp
from lib.socket_udp import CHUNK_SIZE
from lib.package import Package, Header, UPLOAD
from lib.exceptions import AbortedException, TimeOutException

W_SIZE = 5


class Client_udp_gbn(Client_udp):

    def do_upload(self, path, name):

        filesz = self.fmanager.get_size(path)
        seqnum = 0
        sent = 0

        sendq = []
        file_finished = False
        while sent < filesz:
            while len(sendq) < W_SIZE:
                header = Header(seqnum, UPLOAD, path, name, filesz)
                size = CHUNK_SIZE - header.size
                payload = self.fmanager.read_chunk(size, path, how='rb')
                if (len(payload) == 0):
                    file_finished = True
                    break
                pkg = Package(header, payload)
                sendq.append(pkg)
                seqnum += 1

            while len(sendq) >= W_SIZE or (file_finished and len(sendq) > 0):
                for package in sendq:
                    self.socket.send(package, self.address)
                    package.acked = False

                try:
                    waiting_for = len(sendq)
                    while waiting_for > 0:
                        acked, _ = self.socket.recv_with_timer()
                        for package in sendq:
                            if package.header.seqnum == acked.header.seqnum:
                                package.acked = True
                                waiting_for -= 1
                except TimeOutException:
                    pass  # count number of timeouts and abort

                while len(sendq) > 0 and sendq[0].acked:
                    sent += len(sendq[0].payload)
                    sendq.pop()

        self.fmanager.close_file(path)
