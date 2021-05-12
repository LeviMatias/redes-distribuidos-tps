from lib.common import Printer
from lib.printer import QuietPrinter, DefaultPrinter, VerbosePrinter


class ArgParser:

    @staticmethod
    def check_client_side_args(argv):

        '''
        excpected:
            args =
            [upload-file|download-file]
            [-h]
            [-v | -q]
            [-H ADDR ]
            [-p PORT ]
            [-d FILEPATH ]
            [-n FILENAME ]
        '''

        assert len(arv)>0, 'command to short'
        assert argv[0]=='upload-file' or argv[0]=='download-file', 'command name invalid'

        found_addr = False
        found_port = False
        found_file_path = False
        found_file_name = False

        for arg in argv:
            if arg == '-H':
                found_addr = True
            if arg == '-p':
                found_port = True
            if arg == '-d':
                found_file_path = True
            if arg == '-n':
                found_file_name = True

        assert found_addr, 'missing host address'
        assert found_port, 'missing host port'
        assert found_file_path or found_file_name, 'missing file name or path'

    @staticmethod
    def check_server_side_args(argv):

        '''
        excpected:
            args =
            [start-server]
            [-h]
            [-v | -q]
            [-H ADDR ]
            [-p PORT ]
            [-s DIRPATH ]
        '''

        assert len(arv)>0, 'command to short'
        assert argv[0]=='start-server', 'command name invalid'

        found_addr = False
        found_port = False
        found_dir_path = False

        for arg in argv:
            if arg == '-H':
                found_addr = True
            if arg == '-p':
                found_port = True
            if arg == '-s':
                found_dir_path = True

        assert found_addr, 'missing host address'
        assert found_port, 'missing host port'
        assert found_dir_path, 'missing files directory path'

    @staticmethod
    def parse_client_side(argv):

        addr = None
        port = None
        file_path = None
        file_name = None
        printer = DefaultPrinter()

        for i, arg in enumerate(argv):
            if arg == '-h':
                print_client_help()
            if arg == '-v':
                printer = VerbosePrinter()
            if arg == '-q':
                printer = QuietPrinter()
            if arg == '-H':
                addr = argv[i+1]
            if arg == '-p':
                port = argv[i+1]
            if arg == '-d':
                file_path = argv[i+1]
            if arg == '-n':
                file_name = argv[i+1]
        return addr, port, file_path, file_name, printer

    @staticmethod
    def parse_server_side(argv):

        addr = None
        port = None
        dir_path = None
        printer = DefaultPrinter()

        for i, arg in enumerate(argv):
            if arg == '-h':
                print_server_help()
            if arg == '-v':
                printer = VerbosePrinter()
            if arg == '-q':
                printer = QuietPrinter()
            if arg == '-H':
                addr = argv[i+1]
            if arg == '-p':
                port = argv[i+1]
            if arg == '-s':
                dir_path = argv[i+1]
        return addr, port, dir_path, printer

    @staticmethod
    def print_server_help():

        cmd_description = 'server command for providing data transfer of certain file path or name to a host address toghether with its port number'

        print(f'''
        {cmd_description}
            optional arguments :
            -h, --help show this help message and exit
            -v, -- verbose increase output verbosity
            -q, --quiet decrease output verbosity
            -H, --host service IP address
            -p, --port service port
            -s, -- storage storage dir path
        ''')

    @staticmethod
    def print_client_help():

        cmd_description = 'client command for uploading or downloading certain file path or name to a host address toghether with its port number'

        print(f'''
        {cmd_description}
            optional arguments :
            -h, --help show this help message and exit
            -v, -- verbose increase output verbosity
            -q, --quiet decrease output verbosity
            -H, --host server IP address
            -p, --port server port
            -d, --dst destination file path
            -n, --name file name
        ''')
