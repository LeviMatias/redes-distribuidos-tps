import time


class Logger:

    def __init__(self, path):
        self.logfile = open(path + 'log.txt', 'w')

    def log(self, msg):
        t = time.time()
        self.logfile.write(msg+'|'+str(t)+'\n')

    def close(self):
        self.logfile.close()
