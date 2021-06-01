import queue
import time
from threading import Thread


from lib.package import DOWNLOAD, UPLOAD
from lib.exceptions import AbortedException, ConnectionInterrupt, TimeOutException
from lib.package import Package, Header
from lib.socket_udp import server_socket_udp
from lib.socket_udp import CHUNK_SIZE, MAX_TIMEOUTS, CONNECTION_TIMEOUT
from lib.timer import Timer


class Connection_instance:
    def __init__(self, address, fmanager, printer):
        self.socket = server_socket_udp(address[0], address[1])
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
        package.validate()
        self.socket.update_recv_stats(package)
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

        except (AbortedException, ConnectionResetError):
            self.printer.print_connection_lost(self.address)
        except ConnectionInterrupt:
            pass
        except FileNotFoundError:
            if self.in_use_file_path:
                self.printer.print_file_not_found(self.in_use_file_path)
        finally:
            self.close()
            self.printer.print_connection_finished(self.address)
            self.printer.print_duration(time.time() - start)

    def do_upload(self, firts_pckg):

        self.printer._print('GBN and S&W upload')
        name = firts_pckg.header.name
        size = firts_pckg.header.filesz
        path = self.fmanager.SERVER_BASE_PATH + name
        self.in_use_file_path = path

        last_recv_seqnum = -1
        pkg = firts_pckg
        transmition_cmplt = False

        timer = Timer(self.socket.timeout_limit)
        timer.start()
        timeouts = 0
        while self.running and not transmition_cmplt:
            try:
                timer.update()
                if pkg.header.seqnum == last_recv_seqnum + 1:
                    transmition_cmplt, written = self.__reconstruct_file(pkg, path)
                    self.printer.conn_stats(self.socket, written, size)
                    last_recv_seqnum += 1

                self.socket.send_ack(last_recv_seqnum, self.address)

                if transmition_cmplt:
                    self.fmanager.close_file(path)
                    self.close()
                    transmition_cmplt = True
                else:
                    pkg = self.pull()
                    timeouts = 0
                    timer.reset()
            except TimeOutException:
                timeouts += 1
                if timeouts >= MAX_TIMEOUTS:
                    raise AbortedException

        self.printer.print_upload_finished(name)

    def do_download(self, request):

        self.printer._print('S&W download')
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
            self.printer.conn_stats(self.socket, bytes_sent, size)

        self.fmanager.close_file(path)
        self.printer.print_download_finished(name)

    def is_active(self):
        return self.running

    def close(self):
        self.running = False
        self.socket.close()
        if self.in_use_file_path:
            self.fmanager.close_file(self.in_use_file_path)

    def __reconstruct_file(self, package, server_file_path):
        written = self.fmanager.write(server_file_path, package.payload, 'wb')
        return written >= package.header.filesz, written

    def join(self):
        self.thread.join()
