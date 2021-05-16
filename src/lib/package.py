from lib.common import DOWNLOAD, UPLOAD, ABORT


class Header:
    def __init__(self, seqnum, req, name, filesz):
        self.seqnum = seqnum
        self.req = req
        self.namesz = len(name)
        self.filesz = filesz
        self.size = self.namesz + len(filesz) + len(req) + len(seqnum)


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