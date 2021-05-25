import os


class FileManager:

    def __init__(self, dir_path=None):
        self.opened_files = {}

    def open_file(self, path, how):
        f = open(path, how)
        self.opened_files[path] = f
        return f

    def get_file(self, path, how, create=True):
        if path not in self.opened_files and create:
            self.open_file(path, how)
        return self.opened_files[path]

    def write(self, path, data, how='wb'):
        f = self.get_file(path, how)
        f.write(data)
        return f.tell()

    # https://docs.python.org/2.4/lib/bltin-file-objects.html
    # ver metodo 'read([size])'
    def read_chunk(self, chunk_size, path, how='rb'):
        return self.get_file(path, 'rb').read(chunk_size)

    def close_file(self, path):
        file = self.get_file(path, 'rb', create=False)
        if file:
            file.close()
        self.remove(path)

    def get_size(self, path):
        file = self.get_file(path, "rb")
        index = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(index, os.SEEK_SET)
        return size
