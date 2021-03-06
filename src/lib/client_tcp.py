from lib.common import UPLOAD, DOWNLOAD, FileManager
import time


class Client:
    def __init__(self, serv, printer):
        self.serv = serv
        self.printer = printer
        self.file_manager = FileManager()
        self.printer.print_connection_established(serv.addr)

    # upload wrapper
    def upload(self, path, name):
        self.__data_transfer(path, name, self.__client_upload_protocol)

    # download wrapper
    def download(self, path, name):
        self.__data_transfer(path, name, self.__client_download_protocol)

    # actual concrete upload implementation
    def __client_upload_protocol(self, path, name):
        start = time.time()

        # inform the server we want to upload

        self.printer.print_begin_transfer(path)
        self.serv.send(UPLOAD)
        self.serv.wait_ack()

        # send the name to the server
        self.serv.send(name)
        self.serv.wait_ack()

        # send the file size to the server
        file = self.file_manager.open_file(path=path, how='rb')
        size = self.file_manager.get_size(file)
        self.serv.send(str(size))
        self.serv.wait_ack()

        # begin reading and sending data
        self.serv.send_file(file, size, self.printer.progressBar)
        file.close()

        self.printer.print_upload_finished(name)
        self.printer.print_bytes_sent(size)
        self.printer.print_time_elapsed(time.time() - start)

    # actual concrete download implementation
    def __client_download_protocol(self, path, name):
        start = time.time()

        # inform the server we want to upload
        self.printer.print_begin_transfer(path)
        self.serv.send(DOWNLOAD)
        self.serv.wait_ack()

        # send the name to the server
        self.serv.send(path)
        self.serv.wait_ack()

        # wait for the file size from the server
        size = self.serv.wait_for_size()

        # begin reading and sending data
        file = self.file_manager.open_file(path=name, how='wb')
        self.serv.recv_file(file, size, self.printer.progressBar)
        file.close()

        self.printer.print_download_finished(name)
        self.printer.print_bytes_recv(size)
        self.printer.print_time_elapsed(time.time() - start)

    # receives a file path and calls the specified protocol function
    # to process the given file at the path
    def __data_transfer(self, path, name, protocol):
        try:
            protocol(path, name)
        except ValueError:
            self.printer.print_connection_aborted(printStackTrace=False)
        except (ConnectionAbortedError, ConnectionResetError):
            self.printer.print_connection_aborted()
        except FileNotFoundError:
            self.printer.print_file_not_found(path)

    def close(self):
        self.serv.close()
        self.printer.print_connection_finished(self.serv.addr)
        self.printer.print_connection_stats(self.serv.bytes_sent,
                                            self.serv.bytes_recv,
                                            self.serv.time_alive)
