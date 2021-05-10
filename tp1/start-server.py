import sys
from lib.server_tcp import serve
from lib.argument_parser import ArgParser


if __name__ == "__main__":

    ArgParser.check_server_side_args(sys.argv)

    host, port, dir_path, _printer = ArgParser.parse_server_side(sys.argv)

    serve(host, port, dir_path)
