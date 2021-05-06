import socket
from common_tcp import UPLOAD, DOWNLOAD, socket_tcp, FileManager, Printer


class Client:
    def __init__(self, serv):
        self.serv = serv
        self.file_manager = FileManager('client')

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
        file = self.file_manager.open_file(name=file_name, how='r')
        size = self.file_manager.get_size(file)
        self.serv.send(str(size))
        self.serv.wait_ack()

        # begin reading and sending data
        self.serv.send_file(file, size, from_host='client')
        file.close()

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
        file = self.file_manager.open_file(name=file_name, how='w+')
        self.serv.recv_file(file, size, from_host='client')
        file.close()

    def __data_transfer(self, file_path, protocol):
        file_name = self.file_manager.get_name(file_path)
        try:
            protocol(file_name)
        except ConnectionAbortedError:
            Printer.print_connection_aborted()
        except FileNotFoundError:
            path = self.file_manager.get_absolute_path(path=file_path)
            Printer.print_file_not_found(path)

    def close(self):
        self.serv.close()


if __name__ == "__main__":

    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 8080
    serv.connect((host, port))

    client = Client(socket_tcp(serv, (host, port)))
    #client.upload("from_client_test_upload.txt")
    #client.download("from_server_test_download.txt")
    client.upload("from_client_large_file_upload.txt")
    client.close()
