import json
import socket

class Connection:
    def __init__(self, sock: socket.socket, client_name: str, processes: int):
        self.message_buffer = b""
        self.sock = sock
        assert isinstance(client_name, str)
        assert 1 < len(client_name) < 40
        self.client_name = client_name
        assert isinstance(processes, int)
        self.processes = processes
        self.job_id = None