from threading import Thread
import os
import queue
from socket import AF_INET, SOCK_DGRAM, socket
from lib.common import CHUNK_SIZE, DOWNLOAD, UPLOAD, ABORT


class Server_udp:
    def __init__(self, address, port, dir_addr):
        self.address = address
        self.port = port
        self.active_connections = {}
        self.socket = None
        self.fmanager = FileManager(dir_addr)

    def start(self):
        self.create_socket()
        thread = Thread(target=self.listen)
        thread.start()
        thread.join()

    def create_socket(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((self.address, self.port))

    # socket.sendto(OK_ACK, package.src_address)
    def listen(self):
        while(True):
            package = self.get_new_package()
            self.demux(package)

    def get_new_package(self):

        message, address = self.socket.recvfrom(CHUNK_SIZE)
        package = Package.deserealize(message, address)
        return package

    def demux(self, package):
        address = package.get_src_address()

        if address not in self.active_connections:
            self.create_connection_with(address)

        self.active_connections[address].push(package)

    def create_connection_with(self, address):
        conn = Connection_instance(self.socket, address, self.fmanager, self)
        conn.start()
        self.active_connections[address] = conn

    def notify_ended_connection_at(self, address):
        del self.active_connections[address]


class Connection_instance:
    def __init__(self, socket, address, fmanager, server):
        self.server = server
        self.socket = socket
        self.address = address
        self.package_queue = queue.Queue()
        self.fmanager = fmanager
        self.__init_sequnums()
        self.running = False

    def push(self, package):
        self.package_queue.put(package)

    def pull(self):
        return self.package_queue.get()

    def __init_sequnums(self):
        self.current_seqnum = -1
        self.expected_seqnum = self.current_seqnum + 1

    def __update_seqnums(self):
        self.current_seqnum += 1
        self.expected_seqnum = self.current_seqnum + 1

    def __get_next_seqnum(self, seqnum):
        return seqnum + 1

    def start(self):
        self.running = True
        thread = Thread(target=self.dispatch)
        thread.start()
        thread.join()

    # el timer de conexion de implementaria en este loop
    # se envia un abort package al client en el timer interrupt
    def dispatch(self):
        while self.running:
            package = self.pull()
            package.dispatch_to(self)

    # esta garantizado que el package es de tipo upload
    # notar que no importa si es el primer packete o si es uno del medio
    # siempre la operacion es la misma y es consistente
    def do_upload(self, package):
        seqnum = package.get_seqnum()
        if seqnum == self.expected_seqnum:
            self.__reconstruct_file(package)
            self.__update_seqnums()
        self.__send_ack()

    # esta garantizado que el package es de tipo download
    # el paquete download recibido por la conection_instance (lado server)
    # siempre sera un ACK con seqnum del ultimo paquete recibido en orden
    # por el client
    # notar que no importa si es el primer packete o si es uno del medio
    # siempre la operacion es la misma y es consistente
    def do_download(self, package):
        ack_seqnum = package.get_seqnum()
        path = package.get_path()

        if ack_seqnum == self.current_seqnum:
            send_package = self.__extract_next_package(ack_seqnum, path)
            self.__update_seqnums()
            self.__send(send_package)
        else:
            self.__retransmit()

    # esta garantizado que el package es de tipo abort
    # si el ack de no le llega al cliente problema del cliente
    # (hubiese usado TCP y no un protocolo connectionless)
    def do_abort(self, package):
        self.__update_seqnums()
        self.__send_ack()
        self.__close()

    # se asume que el packete no esta identificado porque tiene
    # algun problema de formateo sea por corrupcion o fallo de
    # protocolo
    # se envia ack para pedir reenvio
    def do_recv_unidentified(self, package):
        self.__send_ack()

    def __retransmit(self):
        self.__send(self.last_sent_package)

    def __close(self):
        self.running = False
        self.server.notify_ended_connection_at(self.address)

    def __send(self, package):
        self.last_sent_package = package
        bytestream = Package.serialize(package)
        self.socket.send(bytestream, self.address)

    def __extract_next_package(self, seqnum, path):
        next_seqnum = self.__get_next_seqnum(seqnum)
        payload = self.fmanager.read_chunck(CHUNK_SIZE, path, how='br')
        return Package.create_download(next_seqnum, payload)

    def __reconstruct_file(self, package):
        name = package.get_name()
        path = self.fmanager.absolute_path(name)
        self.fmanager.write(path, 'rb')

    def __send_ack(self):
        ack = Package.create_ack(self.current_seqnum)
        bytestream = Package.serialize(ack)
        self.socket.send(bytestream, self.address)


class Package:

    @staticmethod
    def serialize(package):
        bytestream = None
        return bytestream

    # if no bytestream it returns a 'null_package'
    @staticmethod
    def deserialize(bytestream):
        package = None
        return package

    def __init__(self, header, payload):
        self.header = header
        self.payload = payload

    def dispatch_to(self, connection):
        type = self.get_type()

        if type == DOWNLOAD:
            connection.do_download(self)
        elif type == UPLOAD:
            connection.do_upload(self)
        elif type == ABORT:
            connection.do_abort(self)
        else:
            connection.do_recv_unidentified(self)

    def get_type(self):
        return self.header.get_type()


class FileManager:

    def __init__(self, dir_path=None):
        self.SERVER_BASE_PATH = dir_path
        self.opened_files = {}

    def get_name(self, path):
        return path.split()[-1]

    def open_file(self, path, how):
        f = open(path, how)
        self.opened_files[path] = f
        return f

    def get_file(self, path, how, create=True):
        if path not in self.opened_files and create:
            self.open_file(path, how)
        return self.opened_files[path]

    def write(self, path, data, how='bw'):
        self.get_file(path, how).write(data)

    # https://docs.python.org/2.4/lib/bltin-file-objects.html
    # ver metodo 'read([size])'
    def read_chunck(self, chunck_size, path, how='br'):
        return self.get_file(path, how).read(chunck_size).encode()

    def close(self, path):
        file = self.get_file(path, create=False)
        if file:
            file.close()
        self.remove(path)

    def remove(self, path):
        del self.opened_files[path]

    def get_size(self, path):
        file = self.get_file(path)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0, os.SEEK_SET)
        return size
