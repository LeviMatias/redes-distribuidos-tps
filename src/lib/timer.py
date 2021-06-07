import time
from lib.exceptions import TimeOutException


class Timer:

    def __init__(self, timeout_time):
        self.last_active = None
        self.timeout_time = timeout_time
        self.timming_thread = None
        self.running = False

    def start(self):
        self.last_active = time.time()

    def update(self):
        elapsed = time.time() - self.last_active
        if elapsed >= self.timeout_time:
            raise(TimeOutException)

    def stop(self):
        self.last_active = None

    def reset(self):
        self.stop()
        self.start()
