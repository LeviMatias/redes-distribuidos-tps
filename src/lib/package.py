SEPARATOR = "|"
SEPARATOR_ASCII = 124
HEADER_END = "~"
END_ASCII = 126


class Header:

    def __init__(self, seqnum, req, path, name, filesz):
        self.seqnum = seqnum
        self.req = req
        self.path = path
        self.name = name
        self.filesz = filesz
        self.serialized = (f'{seqnum}'+SEPARATOR+f'{req}' + SEPARATOR +
                           f'{path}' + SEPARATOR +
                           f'{name}'+SEPARATOR+f'{filesz}'+HEADER_END)
        self.size = len(self.serialized)


class Package:

    @staticmethod
    def serialize(package):
        return (package.header.serialized.encode() + package.payload)

    @staticmethod
    def deserialize(bytestream):
        fields = []

        start = 0
        end = 0
        for elem in bytestream:
            if elem == SEPARATOR_ASCII or elem == END_ASCII:
                fields.append(bytestream[start:end])
                start = end + 1
            if elem == END_ASCII:
                fields.append(bytestream[start:])
                break
            end += 1

        header = Header(int(fields[0]),  # seqnum
                        fields[1].decode(),  # request type
                        fields[2].decode(),  # path
                        fields[3].decode(),  # filename
                        int(fields[4]))  # filesize

        return Package(header, fields[-1])

    @staticmethod
    def create_ack(num):  # todo recv ok_ack as param?
        h = Header(num, "ACK", "", "", 0)
        return Package(h, ("").encode())

    def __init__(self, header, payload):
        self.header = header
        self.payload = payload

    def get_type(self):
        return self.header.req
