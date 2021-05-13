from lib.common import UPLOAD, DOWNLOAD, FileManager
import time


class Client:
    def __init__(self, serv, printer):
        self.serv = serv
        self.printer = printer
        self.file_manager = FileManager('client')
        self.printer.print_connection_established(serv.addr)

    # upload wrapper
    def upload(self, file_path):
        self.__data_transfer(file_path, self.__client_upload_protocol)

    # download wrapper
    def download(self, file_path):
        self.__data_transfer(file_path, self.__client_download_protocol)

    # actual concrete upload implementation
    def __client_upload_protocol(self, file_name):
        start = time.time()

        # inform the server we want to upload

        self.printer.print_begin_transfer(file_name)
        self.serv.send(UPLOAD)
        self.serv.wait_ack()

        # send the name to the server
        self.serv.send(file_name)
        self.serv.wait_ack()

        # send the file size to the server
        file = self.file_manager.open_file(name=file_name, how='rb')
        size = self.file_manager.get_size(file)
        self.serv.send(str(size))
        self.serv.wait_ack()

        # begin reading and sending data
        self.serv.send_file(file, size, self.printer.progressBar)
        file.close()

        self.printer.print_bytes_sent(size)
        self.printer.print_time_elapsed(time.time() - start)

    # actual concrete download implementation
    def __client_download_protocol(self, file_name):
        start = time.time()

        # inform the server we want to upload
        self.printer.print_begin_transfer(file_name)
        self.serv.send(DOWNLOAD)
        self.serv.wait_ack()

        # send the name to the server
        self.serv.send(file_name)
        self.serv.wait_ack()

        # wait for the file size from the server
        size = self.serv.wait_for_size()

        # begin reading and sending data
        file = self.file_manager.open_file(name=file_name, how='wb')
        self.serv.recv_file(file, size, self.printer.progressBar)
        file.close()

        self.printer.print_bytes_recv(size)
        self.printer.print_time_elapsed(time.time() - start)

    # receives a file path and calls the specified protocol function
    # to process the given file at the path
    def __data_transfer(self, file_path, protocol):
        file_name = self.file_manager.get_name(file_path)
        try:
            protocol(file_name)
        except (ConnectionAbortedError, ConnectionResetError):
            self.printer.print_connection_aborted()
        except FileNotFoundError:
            path = self.file_manager.get_absolute_path(file_path)
            self.printer.print_file_not_found(path)

    def close(self):
        self.serv.close()
        self.printer.print_connection_finished(self.serv.addr)
        self.printer.print_connection_stats(self.serv.bytes_sent,
                                            self.serv.bytes_recv,
                                            self.serv.time_alive)
