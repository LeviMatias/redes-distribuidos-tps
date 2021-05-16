import socket
import os
import time

UPLOAD = 1
DOWNLOAD = 0
CHUNK_SIZE = 1024
OK_ACK = "Ok"
TIMEOUT = 5

 # headr: secnum, request, lnombre, nombre, lfile, size
 # payload: sz: CHUNKSIZE - headrsz;
 # ack_headr: last_ack_secnum, 0, 0, 0

 class protocol:

    def send(self, data, address):
        socket.send(data)
     
    def recv_file(self):

        read_header()
        
  
    def recv(self,):