from threading import Thread
import time

from lib.connection_instance import Connection_instance
from lib.socket_udp import server_socket_udp

CLEANER_WAIT_TIME = 1


class Server_udp:
    def __init__(self, address, port, base_dir_path, printer):
        self.address = address
        self.port = port
        self.socket = None

        self.active_connections = {}

        self.printer = printer
        self.base_dir_path = base_dir_path

    def run(self):
        try:
            self.create_socket()
            listener = self.start_listener()
            sender = self.start_sender()
            self.periodic_clean()
        except KeyboardInterrupt:
            if listener:
                listener.join()
            if sender:
                sender.join()
            self.close_connections()

    def create_socket(self):
        self.socket = server_socket_udp(self.address, self.port)
        self.socket.bind()

    def close_connection(self):
        for dst_addr, conn_instance in self.active_connections.items():
            conn_instance.close()
            conn_instance.join()
            del self.active_connections[dst_addr]

    def start_listener(self):
        thread = Thread(target=self.listen)
        thread.start()
        return thread

    def start_sender(self):
        thread = Thread(target=self.send)
        thread.start()
        return thread

    def start_cleaner(self):
        thread = Thread(target=self.periodic_clean)
        thread.start()
        return thread

    def listen(self):
        while(True):
            package, address = self.socket.blocking_recv()
            self.demux(package, address)

    def send(self):
        for dst_addr, conn_instance in self.active_connections.items():
            while conn_instance.has_to_send():
                package = conn_instance.pull_from_send()
                self.socket.send(package, dst_addr)

    def demux(self, package, dst_addr):
        if dst_addr not in self.active_connections:
            self.create_connection_with(dst_addr)

        self.active_connections[dst_addr].push_to_recv(package)

    def create_connection_with(self, dst_addr):
        c = Connection_instance(self.socket, dst_addr, self.printer,
                                self.base_dir_path)
        c.start()
        self.active_connections[dst_addr] = c

    def periodic_clean(self):
        while True:
            time.sleep(CLEANER_WAIT_TIME)
            for dst_addr, conn_instance in self.active_connections.items():
                if not conn_instance.is_active():
                    conn_instance.join()
                    del self.active_connections[dst_addr]
