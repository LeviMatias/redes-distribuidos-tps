from threading import Thread
import time

from lib.socket_udp import server_socket_udp
from lib.server_udp_gbn import Connection_instance_udp_gbn
from lib.file_manager import FileManager
from lib.socket_udp import CONNECTION_TIMEOUT
from lib.package import AbortPackage
from lib.common import EXIT


class Server_udp:
    def __init__(self, address, port, dir_addr, printer):
        self.address = address
        self.port = port
        self.active_connections = {}
        self.socket = None
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
        except KeyboardInterrupt:
            pass

    def demux(self, package, address):

        if not package or not address:
            return

        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, addr):
        c = Connection_instance_udp_gbn(addr, self.fmanager, self.printer)
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
            time.sleep(CONNECTION_TIMEOUT)

            dead_connections = {}
            for addr, connection in self.active_connections.items():
                if not connection.is_active():
                    connection.push(AbortPackage())
                    connection.join()
                    dead_connections[addr] = connection

            for addr in dead_connections:
                del self.active_connections[addr]

    def close(self):
        self.running = False
        for addr, connection in self.active_connections.items():
            connection.push(AbortPackage())
            connection.join()

        self.socket.close()

        if self.cleaner:
            self.cleaner.join()
        if self.listener:
            self.listener.join()
        self.printer.print_program_closed()
