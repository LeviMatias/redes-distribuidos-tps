import traceback
import time
import os


class QuietPrinter:

    def __init__(self):
        self.printed = []

    def _print(self, msg, store_msg=True):
        print(msg+'\n')
        if store_msg:
            self.printed.append(msg)

    def print_file_not_found(self, path=None, printStackTrace=False):
        if path:
            self._print('File not found at: ' + path)
        if printStackTrace:
            traceback.print_exc()

    def print_connection_lost(self, addr):
        self._print("Connection "+addr[0]+":"+str(addr[1]))

    def print_connection_interrupted(self, addr):
        self._print("Connection "+addr[0]+":"+str(addr[1]))

    def print_connection_aborted(self, printStackTrace=False):
        self._print('An error ocurred. Connection closed')
        if printStackTrace:
            traceback.print_exc()

    def print_program_closed(self):
        self._print('Exited')

    def print_connection_established(self, addr):
        pass

    def print_connection_finished(self, addr):
        pass

    def print_listening_on(self, addr):
        pass

    def print_begin_transfer(self, filename):
        pass

    def print_duration(self, duration):
        pass

    def print_progress(self, sock_stats, progress, filesz):
        pass

    def print_download_finished(self, filename):
        self._print("Download of "+filename+" finished")

    def print_upload_finished(self, filename):
        self._print("Upload of "+filename+" finished")

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _reprint_prev_prints(self):
        for msg in self.printed:
            self._print(msg, store_msg=False)


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

    def print_progress(self, sock_stats, progress, filesz):

        barLength = 20

        now = time.time()

        sent = sock_stats.t_bytes_sent
        sent_ok = sock_stats.t_bytes_sent_ok
        bytes_recvd = sock_stats.t_bytes_recv

        pkgs_sent = sock_stats.pkg_sent
        acks_rcvd = sock_stats.acks_recv
        pkgs_rcvd = sock_stats.pkg_recvd

        elapsed = now - sock_stats.begin_time
        remaning = filesz - progress
        transfer_speed = progress/elapsed if elapsed != 0 else 0

        if transfer_speed != 0:
            eta = round((remaning/transfer_speed)/60, 2)
        else:
            eta = '???'

        ratio = float(progress) / filesz
        percent = round(ratio * 100, 1)
        arrow = '-' * int(round(ratio * barLength, 0)) + '>'
        spaces = ' ' * (barLength - len(arrow))

        # return

        self._clear_screen()
        self._reprint_prev_prints()

        print(f"""
            ______
            bytes sent: {round(sent/1024,2)} KB
            bytes sent acked: {round(sent_ok/1024,2)} KB
            bytes recvd: {round(bytes_recvd/1024,2)} KB

            pkgs sent: {pkgs_sent}
            ACK recvd: {acks_rcvd}
            pkgs recvd: {pkgs_rcvd}

            elapsed: {round(elapsed, 1)} secs
            ETA: {eta} mins
            Progress: [{arrow}{spaces}] {percent}%
            ______
        \n""")
