import traceback


class QuietPrinter:
    def __print(msg):
        print(msg)
        print()

    def print_connection_aborted(self):
        self.__print('An error ocurred. Connection closed')
        traceback.print_exc()

    def print_file_not_found(self, path):
        self.__print('File not found at: ' + path)
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
        self.__print(msg)

    def print_connection_finished(self, addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " finished"
        self.__print(msg)

    def print_listening_on(self, addr):
        self.__print("listening on " + addr[0] + ":" + str(addr[1]))


class VerbosePrinter(DefaultPrinter):

    def print_begin_transfer(self, filename):
        self.__print("Begin of transfer sequence for: " + filename)

    def print_bytes_sent(self, b):
        self.__print("Bytes sent: " + str(b))

    def print_bytes_recv(self, b):
        self.__print("Bytes recv: " + str(b))

    def print_time_elapsed(self, time_in_seconds):
        self._print("Time elapsed: " + str(time_in_seconds) + " seconds")

    def print_connection_stats(self, total_sent, total_recv, conn_dur_in_secs):
        self.__print(" ___________ ")
        self._print(" Total bytes sent: " + str(total_sent))
        self._print(" Total bytes recvd: " + str(total_recv))
        self._print(" Total connection duration: " + str(conn_dur_in_secs))
    
    def progressBar(self, current, total, barLength=20):
        percent = float(current) * 100 / total
        arrow = '-' * int(percent/100 * barLength - 1) + '>'
        spaces = ' ' * (barLength - len(arrow))

        print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')
