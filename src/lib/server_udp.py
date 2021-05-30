from threading import Thread
import time

from lib.socket_udp import server_socket_udp
from lib.server_udp_gbn import Server_udp_gbn
from lib.file_manager import FileManager
from lib.socket_udp import CONNECTION_TIMEOUT
from lib.package import AbortPackage


class Server_udp:
    def __init__(self, address, port, dir_addr, printer):
        self.address = address
        self.port = port
        self.active_connections = {}
        self.socket = None
        self.fmanager = FileManager(dir_addr)
        self.printer = printer

    def run(self):
        self.create_socket()
        self._setup_cleaner()
        self.listen()

    def create_socket(self):
        self.socket = server_socket_udp(self.address, self.port)
        self.socket.bind()

    def listen(self):
        self.printer.print_listening_on((self.address, self.port))
        while(True):
            try:
                package, address = self.socket.blocking_recv()
                self.demux(package, address)
            except ConnectionResetError:
                pass
        self.printer.print_connection_stats(self.socket)

    def demux(self, package, address):
        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, addr):
        c = Server_udp_gbn(addr, self.fmanager, self.printer)
        c.start()
        self.active_connections[addr] = c

    def _setup_cleaner(self):
        Thread(target=self._periodic_clean).start()

    def _periodic_clean(self):
        while True:
            time.sleep(CONNECTION_TIMEOUT)

            dead_connections = {}
            for addr, connection in self.active_connections.items():
                if not connection.is_active():
                    connection.push(AbortPackage())
                    connection.join()
                    self.printer.print_connection_stats(self.socket)
                    dead_connections[addr] = connection

            for addr in dead_connections:
                del self.active_connections[addr]
