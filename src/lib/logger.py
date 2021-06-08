import time


class Logger:

    def __init__(self, path):
        self.logfile = open(path + 'log.txt', 'w')

    def log(self, msg):
        try:
            t = time.time()
            self.logfile.write(msg+'|'+str(t)+'\n')
        except ValueError:
            pass

    def close(self):
        self.logfile.close()
