from threading import Thread
import time
from lib.exceptions import TimeOutException


class Timer:

    def __init__(self, timeout_time):
        self.last_active = None
        self.timeout_time = timeout_time
        self.timming_thread = None
        self.running = False

    def start(self):
        self.running = True
        self.timming_thread = Thread(target=self.update)
        self.last_active = time.time()
        self.timming_thread.start()

    def update(self):
        self.running = True
        while self.running:
            elapsed = time.time() - self.last_active
            if elapsed >= self.timeout_time:
                raise(TimeOutException)

    def stop(self):
        self.running = False
        self.last_active = time.time()
        if self.timming_thread:
            self.timming_thread.join()

    def reset(self):
        self.stop()
        self.start()
