import time
from lib.exceptions import TimeOutException
from threading import Thread


class Timer():
    def __init__(self, timeout_time):
        self.last_active = None
        self.timeout_time = timeout_time

    def set(self):
        self.last_active = time.time()
        self.timming_thread = Thread(target=self.update)
        self.timming_thread.start()

    def update(self):
        elapsed = time.time() - self.last_active
        if elapsed >= self.timeout_time:
            raise(TimeOutException)
        else:
            self.last_active = time.time()

    def stop(self):
        if self.timming_thread:
            self.timming_thread.join()
