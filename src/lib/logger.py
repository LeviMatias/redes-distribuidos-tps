

class Logger:

    def __init__(self, path):
        self.logfile = open(path + 'log.txt', 'w')

    def log(self, msg):
        self.logfile.write(msg+'\n')

    def close(self):
        self.logfile.close()
