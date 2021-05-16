import socket
import time
import queue
from threading import Thread
from lib.common import UPLOAD, DOWNLOAD, socket_tcp, FileManager, package

ABORT_PACKAGE = -1

class connection_instance:
    def __init__(self, socket, addr):
        self.q = queue.Queue()
        self.addr = addr
        self.socket = socket
        self.current_seqnum = 0
        self.expected_seqnum = 1
        self.last_update = time.time()

    def pull(self):
        elem = self.q.get()
        if elem == ABORT_PACKAGE:
            raise ConnectionAbortedError
        return elem

    def push(self, data):
        self.q.push(data)

    def send_ack_ok(self):
        pass

    def _get_next_package(self):
        seqnum = -1
        package = None
        while (seqnum != self.expected_seqnum):
            send_ack_ok(self.current_seqnum)
            package = self.pull()
            seqnum, = package.sequnum
            self.last_update = time.time()

        self.expected_seqnum += 1
        self.current_seqnum += 1
        send_ack_ok(self.current_seqnum)
        return package

    def _upload_protocol(self, path, size):
        file = open(path,'bw')
        
        bytesrcv = 0
        while bytesrcv < size:
            package = self._get_next_package() 
            bytesrcv += package.payload_size
          

    # choose handler for the request
    def dispatch_request(self, package):

        if package.request == UPLOAD:
            self._upload_protocol(package.path, package.size)
        elif package.request == DOWNLOAD:
            self._download_protocol(package.path, package.size)
        else:
            raise(ConnectionAbortedError)

    def listen_request(self):
        validreq = False;
        while not validreq:
            request = self.wait_on_q()
            
            validreq =  self.dispatch_request(request);
            if not validreq:
                 send_ack_ok(-1)

    def run(self):
        self.thread = Thread(target=self.listen_request)
        self.thread.start()

#serve

def serve(host, port, dir_path, printer):
    addr = (host, port)
    active_connections = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(addr)

        while True:
            data, addr = sock.recv()
            # cull list from dead connections
            active_connections[:] = [c for c in active_connections
                                     if not c.finished()]

            if data:
                if not addr in active_connections:
                    ci = connection_instance(addr)
                    ci.run()
                    active_connections[addr] = ci
                ci.push(data)

    except KeyboardInterrupt:

        if sock:
            sock.close()
            for cli in active_connections:
                cli.close()