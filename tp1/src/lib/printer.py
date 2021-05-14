import traceback


class QuietPrinter:
    def _print(self, msg):
        print(msg)
        print()

    def print_connection_aborted(self, printStackTrace=False):
        self._print('An error ocurred. Connection closed')
        if printStackTrace:
            traceback.print_exc()

    def print_file_not_found(self, path=None):
        if path:
            self._print('File not found at: ' + path)
        traceback.print_exc()

    def print_connection_established(self, addr):
        pass

    def print_connection_finished(self, addr):
        pass

    def print_listening_on(self, addr):
        pass

    def progressBar(self, current, total, barLength=20):
        pass

    def print_bytes_sent(self, b):
        pass

    def print_bytes_recv(self, b):
        pass

    def print_time_elapsed(self, time_in_seconds):
        pass

    def print_connection_stats(self, total_sent, total_recv, conn_dur_in_secs):
        pass

    def print_begin_transfer(self, filename):
        pass


class DefaultPrinter(QuietPrinter):

    def print_connection_established(self, addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " started"
        self._print(msg)

    def print_connection_finished(self, addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " finished"
        self._print(" ______ ")
        self._print(msg)

    def print_begin_transfer(self, filename):
        self._print("Begin of transfer sequence for: " + filename)

    def print_listening_on(self, addr):
        self._print("listening on " + addr[0] + ":" + str(addr[1]))


class VerbosePrinter(DefaultPrinter):

    def print_bytes_sent(self, b):
        self._print("Bytes sent: " + str(b))

    def print_bytes_recv(self, b):
        self._print("Bytes recv: " + str(b))

    def print_time_elapsed(self, time_in_seconds):
        self._print("Time elapsed: " + str(time_in_seconds) + " seconds")

    def print_connection_stats(self, total_sent, total_recv, conn_dur_in_secs):

        self._print(" Total bytes sent: " + str(total_sent))
        self._print(" Total bytes recvd: " + str(total_recv))
        self._print(" Total connection duration: " +
                    str(conn_dur_in_secs) + " seconds")
        self._print(" ______ ")

    def progressBar(self, current, total, barLength=20):
        ratio = float(current) / total
        percent = round(ratio * 100, 1)
        arrow = '-' * int(round(ratio * barLength, 0)) + '>'
        spaces = ' ' * (barLength - len(arrow))

        print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')
