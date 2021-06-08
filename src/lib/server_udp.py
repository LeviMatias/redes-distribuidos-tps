import time
from threading import Thread
from lib.file_manager import FileManager
from lib.package import AbortPackage, InterruptPackage
from lib.socket_udp import server_socket_udp
from lib.connection_instance import Connection_instance
from lib.common import EXIT
from lib.connection_instance_gbn import Connection_instance_gbn


class Server_udp:
    def __init__(self, address, port, dir_addr, printer, gbn):
        self.gbn = gbn
        self.address = address
        self.port = port
        self.socket = None
        self.active_connections = {}
        self.fmanager = FileManager(dir_addr)
        self.printer = printer
        self.running = False

        self.listener = None
        self.cleaner = None

    def run(self):
        self.running = True
        self.create_socket()
        self._setup_cleaner()
        self._setup_listener()
        self._read_input()

    def create_socket(self):
        self.socket = server_socket_udp(self.address, self.port)
        self.socket.bind()

    def listen(self):
        self.printer.print_listening_on((self.address, self.port))
        try:
            while self.running:
                package, address = self.socket.blocking_recv()
                self.demux(package, address)
        except ConnectionResetError:
            self.printer.print_connection_lost(self.address)

    def demux(self, package, address):

        if not package or not address:
            return

        if address not in self.active_connections:

            is_ongoing_stream = package.header.seqnum > 0
            if is_ongoing_stream:
                return
            else:
                self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, addr):
        c = None
        if self.gbn:
            c = Connection_instance_gbn(addr, self.fmanager, self.printer)
        else:
            c = Connection_instance(addr, self.fmanager, self.printer)
        c.start()
        self.active_connections[addr] = c

    def _setup_listener(self):
        self.listener = Thread(target=self.listen)
        self.listener.start()

    def _setup_cleaner(self):
        self.cleaner = Thread(target=self._periodic_clean)
        self.cleaner.start()

    def _read_input(self):
        while self.running:
            read_from_stdin = input()
            if read_from_stdin == EXIT:
                self.running = False
        self.close()

    def _periodic_clean(self):
        while self.running:
            time.sleep(0.1)
            abortpckg = AbortPackage()

            dead = {}

            for addr, c in self.active_connections.items():
                if not c.is_active():
                    c.push(abortpckg)
                    dead[addr] = c

            for addr, c in dead.items():
                c.join()
                del self.active_connections[addr]

            #self.active_connections = {addr: c for addr, c
                                       #in self.active_connections.items()
                                       #if c.is_active() or c.push(abortpckg)
                                       #or c.join()}

    def close(self):
        self.running = False
        for addr, connection in self.active_connections.items():
            connection.push(InterruptPackage())
            connection.join()

        self.socket.close()

        if self.cleaner:
            self.cleaner.join()
        if self.listener:
            self.listener.join()
        self.printer.print_program_closed()
