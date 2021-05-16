import os

UPLOAD = "Upload"
DOWNLOAD = "Download"
CHUNK_SIZE = 1024
OK_ACK = "Ok"
ABORT = 'Abort'


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