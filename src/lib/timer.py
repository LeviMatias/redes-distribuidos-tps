import time


class Timer:

    def __init__(self, timeout_time, timeoutException):
        self.last_active = None
        self.timeout_time = timeout_time
        self.timming_thread = None
        self.running = False
        self.excpt = timeoutException

    def start(self):
        self.last_active = time.time()

    def update(self):
        elapsed = time.time() - self.last_active
        if elapsed >= self.timeout_time:
            raise(self.excpt)

    def stop(self):
        self.last_active = None

    def reset(self):
        self.stop()
        self.start()
