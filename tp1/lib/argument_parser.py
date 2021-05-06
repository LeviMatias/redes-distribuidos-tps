from lib.common import Printer


class ArgParser:

    @staticmethod
    def check_client_side_args(argv):

        '''
        excpected:
            args =
            [file-upload|file-download]
            [-h]
            [-v | -q]
            [-H ADDR ]
            [-p PORT ]
            [-d FILEPATH ]
            [-n FILENAME ]
        '''

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
            [start - server]
            [-h]
            [-v | -q]
            [-H ADDR ]
            [-p PORT ]
            [-s DIRPATH ]
        '''

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

        for i, arg in enumerate(argv):
            if arg == '-h':
                Printer.print_client_help()
            if arg == '-v':
                pass
                #TODO se vuelve mas verboso sea lo que sea que signifique eso
            if arg == '-q':
                pass
                #TODO se vuelve menos verboso sea lo que sea que signifique eso
            if arg == '-H':
                addr = argv[i+1]
            if arg == '-p':
                port = argv[i+1]
            if arg == '-d':
                file_path = argv[i+1]
            if arg == '-n':
                file_name = argv[i+1]
        return addr, port, file_path, file_name

    @staticmethod
    def parse_server_side(argv):

        addr = None
        port = None
        dir_path = None

        for i, arg in enumerate(argv):
            if arg == '-h':
                Printer.print_server_help()
            if arg == '-v':
                pass
                #TODO se vuelve mas verboso sea lo que sea que signifique eso
            if arg == '-q':
                pass
                #TODO se vuelve menos verboso sea lo que sea que signifique eso
            if arg == '-H':
                addr = argv[i+1]
            if arg == '-p':
                port = argv[i+1]
            if arg == '-s':
                dir_path = argv[i+1]
        return addr, port, dir_path
