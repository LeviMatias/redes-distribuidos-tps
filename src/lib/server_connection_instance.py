from lib.connection_instance import Connection_instance


class Server_connection_instance (Connection_instance):

    def __init__(self) -> None:
        super().__init__()

        self.connection_thread = None
