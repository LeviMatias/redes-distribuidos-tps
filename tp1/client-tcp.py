import socket
from common_tcp import UPLOAD, DOWNLOAD, socket_tcp, FileManager


class Client:
    def __init__(self, serv):
        self.serv = serv

    def upload(self, file_path):
        self.__data_transfer(file_path, self.__client_upload_protocol)

    def download(self, file_path):
        self.__data_transfer(file_path, self.__client_download_protocol)

    def __client_upload_protocol(self, file_name):

        # inform the server we want to upload
        self.serv.send(UPLOAD)
        self.serv.wait_ack()

        # send the name to the server
        self.serv.send(file_name)
        self.serv.wait_ack()

        # send the file size to the server
        size = FileManager.get_size(file_name=file_name)
        self.serv.send(str(size))
        self.serv.wait_ack()

        # begin reading and sending data
        self.serv.send_file(file_name, size)

    def __client_download_protocol(self, file_name):
        # inform the server we want to upload
        self.serv.send(DOWNLOAD)
        self.serv.wait_ack()

        # send the name to the server
        self.serv.send(file_name)
        self.serv.wait_ack()

        # wait for the file size from the server
        size = self.serv.wait_for_size()

        # begin reading and sending data
        self.serv.recive_file(file_name, size)

    def __data_transfer(self, file_path, protocol):
        file_name = FileManager.get_name(file_path)
        try:
            protocol(file_name)
        except ConnectionAbortedError:
            print("An error ocurred and the connection was closed")
        except FileNotFoundError:
            print("No such file: ", FileManager.get_absolute_path(file_path))
        self.close()

    def close(self):
        self.serv.close()


if __name__ == "__main__":
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 8080
    serv.connect((host, port))

    client = Client(socket_tcp(serv, (host, port)))
    client.upload("test.txt")
    client.close()
