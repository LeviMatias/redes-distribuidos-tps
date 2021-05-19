SEPARATOR = "|"


class Header:

    def __init__(self, seqnum, req, name, filesz):
        self.seqnum = seqnum
        self.req = req
        self.name = name
        self.filesz = filesz
        self.serialized = (f'{seqnum}'+SEPARATOR+f'{req}' + SEPARATOR +
                           f'{name}'+SEPARATOR+f'{filesz}'+SEPARATOR)
        self.size = len(self.serialized)


class Package:

    @staticmethod
    def serialize(package):
        return (package.header.serialized + str(package.payload)).encode()

    @staticmethod
    def deserialize(bytestream):
        bytestream = str(bytestream)
        fields = bytestream.split(SEPARATOR)
        header = Header(fields[0], fields[1], fields[2], fields[3])

        return Package(header, fields[4].encode())

    @staticmethod
    def create_ack(num):  # todo recv ok_ack as param?
        h = Header(num, "ACK", "", 0)
        return Package(h, ("").encode())

    def __init__(self, header, payload):
        self.header = header
        self.payload = payload

    def get_type(self):
        return self.header.req
