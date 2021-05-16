
class Header:
    def __init__(self, seqnum, req, name, filesz):
        self.seqnum = seqnum
        self.req = req
        self.namesz = len(name)
        self.filesz = filesz
        self.size = self.namesz + len(filesz) + len(req) + len(seqnum)

"name|size|payload"

class Package:
    def __init__(self, header, payload) -> None:
        self.header = header
        self.payload = payload

    @staticmethod
    def Process(data):
        
