import traceback


class QuietPrinter:
    def _print(self, msg):
        print(msg)
        print()

    def print_connection_aborted(self, printStackTrace=False):
        self._print('An error ocurred. Connection closed')
        if printStackTrace:
            traceback.print_exc()

    def print_file_not_found(self, path=None, printStackTrace=False):
        if path:
            self._print('File not found at: ' + path)
        if printStackTrace:
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

    def print_connection_stats(self, sock_stats):
        pass

    def print_begin_transfer(self, filename):
        pass

    def print_download_finished(self, filename):
        self._print("Download of "+filename+" finished")

    def print_upload_finished(self, filename):
        self._print("Upload of "+filename+" finished")

    def print_connection_lost(self, addr):
        self._print("Connection "+addr[0]+":"+str(addr[1]) +
                    " lost: no answer - too many timeouts")

    def print_duration(self, duration):
        pass

    def print_timeout():
        pass


class DefaultPrinter(QuietPrinter):

    def print_connection_established(self, addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " started"
        self._print(msg)

    def print_connection_finished(self, addr):
        msg = "connection with " + addr[0] + ":" + str(addr[1]) + " finished"
        self._print(msg)

    def print_begin_transfer(self, filename):
        self._print("Begin of transfer sequence for: " + filename)

    def print_listening_on(self, addr):
        self._print("listening on " + addr[0] + ":" + str(addr[1]))

    def print_duration(self, duration):
        self._print("Process duration: "+str(duration)+" seconds")


class VerbosePrinter(DefaultPrinter):

    def print_timeout(self):
        self._print("timeout!")

    def print_bytes_sent(self, b):
        self._print("Bytes sent: " + str(b))

    def print_bytes_recv(self, b):
        self._print("Bytes recv: " + str(b))

    def print_time_elapsed(self, time_in_seconds):
        self._print("Time elapsed: " + str(time_in_seconds) + " seconds")

    def print_connection_stats(self, sock_stats):
        self._print(" ______ ")
        addr = sock_stats.address
        self._print(" Connection with " + addr + ":" + str(sock_stats.port))
        sent = sock_stats.t_bytes_sent
        sent_ok = sock_stats.t_bytes_sent_ok
        self._print(" Total bytes sent: " + str(sent))
        self._print(" Total bytes sent ACK'd: " + str(sent_ok))
        self._print(" Total bytes recvd: " + str(sock_stats.t_bytes_recv))
        self._print(" Total times timed out: " + str(sock_stats.t_timeouts))

        if sent > 0:
            self._print(" Estimated payload send fail rate: "
                        + str(round(100 - 100 * sent_ok/sent, 2))+"%")
        self._print(" ______ ")

    def progressBar(self, current, total, barLength=20):
        ratio = float(current) / total
        percent = round(ratio * 100, 1)
        arrow = '-' * int(round(ratio * barLength, 0)) + '>'
        spaces = ' ' * (barLength - len(arrow))

        print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')
