from lib.printer import QuietPrinter, DefaultPrinter, VerbosePrinter


class ArgParser:

    @staticmethod
    def parse_path(path):
        if (path[-1] == '/' or path[-1] == '\\'):
            return path
        if (path[0] == '.'):
            return path + path[1]

        return path + path[0]

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
            [-d or -s FILEPATH ]
            [-n FILENAME ]
        '''

        assert len(argv) > 0, 'command to short'

        found_addr = False
        found_port = False
        found_file_path = False
        found_file_name = False

        for arg in argv:
            if arg == '-h' or arg == '--help':
                return
            if arg == '-H' or arg == '--host':
                found_addr = True
            if arg == '-p' or arg == '--port':
                found_port = True
            if arg == '-s' or arg == "--src" or arg == '-d' or arg == "--dst":
                found_file_path = True
            if arg == '-n' or arg == "--name":
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

        assert len(argv) > 0, 'command to short'

        found_addr = False
        found_port = False
        found_dir_path = False

        for arg in argv:
            if arg == '-h' or arg == '--help':
                return
            if arg == '-H' or arg == '--host':
                found_addr = True
            if arg == '-p' or arg == '--port':
                found_port = True
            if arg == '-s' or arg == '--storage':
                found_dir_path = True

        assert found_addr, 'missing host address'
        assert found_port, 'missing host port'
        assert found_dir_path, 'missing files directory path'

    @staticmethod
    def parse_client_side(argv):

        help = False
        addr = None
        port = None
        file_path = None
        file_name = None
        gbn = False
        printer = DefaultPrinter()

        for i, arg in enumerate(argv):
            if arg == '-h' or arg == '--help':
                if argv[0] == 'upload-file':
                    ArgParser.print_upload_help()
                elif argv[0] == 'download-file':
                    ArgParser.print_download_help()
                help = True
            if arg == '-v' or arg == '--verbose':
                printer = VerbosePrinter()
            if arg == '-q' or arg == '--quiet':
                printer = QuietPrinter()
            if arg == '-H' or arg == '--host':
                addr = argv[i+1]
            if arg == '-p' or arg == '--port':
                port = int(argv[i+1])
            if arg == '-d' or arg == "--dst" or arg == '-s' or arg == "--src":
                file_path = argv[i+1]
            if arg == '-n' or arg == "--name":
                file_name = argv[i+1]
            if arg == '-gbn':
                gbn = True
        return help, addr, port, file_path, file_name, printer, gbn

    @staticmethod
    def parse_server_side(argv):

        help = False
        addr = None
        port = None
        dir_path = None
        gbn = False
        printer = DefaultPrinter()

        for i, arg in enumerate(argv):
            if arg == '-h' or arg == '--help':
                ArgParser.print_server_help()
                help = True
            if arg == '-v' or arg == '--verbose':
                printer = VerbosePrinter()
            if arg == '-q' or arg == '--quiet':
                printer = QuietPrinter()
            if arg == '-H' or arg == '--host':
                addr = argv[i+1]
            if arg == '-p' or arg == '--port':
                port = int(argv[i+1])
            if arg == '-s' or arg == '--src':
                dir_path = ArgParser.parse_path(argv[i+1])
            if arg == '-gbn':
                gbn = True
        return help, addr, port, dir_path, printer, gbn

    @staticmethod
    def print_server_help():

        cmd_description = '''
        server command for providing data transfer of certain
         file path or name to a host address toghether with its port number
         '''

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
    def print_download_help():

        cmd_description = '''client command for downloading certain
         file path or name to a host address toghether with its port number
         '''

        print(f'''
        {cmd_description}
            optional arguments :
            -h, --help show this help message and exit
            -v, -- verbose increase output verbosity
            -q, --quiet decrease output verbosity
            -H, --host server IP address
            -p, --port server port
            -d, --destination file path
            -n, --name file name
        ''')

    @staticmethod
    def print_upload_help():

        cmd_description = '''client command for uploading certain
         file path or name to a host address toghether with its port number
         '''

        print(f'''
        {cmd_description}
            optional arguments :
            -h, --help show this help message and exit
            -v, -- verbose increase output verbosity
            -q, --quiet decrease output verbosity
            -H, --host server IP address
            -p, --port server port
            -s, --source file path
            -n, --name file name
        ''')
