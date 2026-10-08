import socket
import json
from hashlib import md5
import multiprocessing

class Client:
    def __init__(self):
        self.version = "1"
        self.port = 50505
        self.server_ip = "127.0.0.1"
        self.client_name = "Roy's computer"
        self.servers_name = ""
        self.hash_md5 = ""
        self.start = 0
        self.end = 0
        self.processes = 8
        self.buffer = b""
        self.connect_to_server()

    def connect_to_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
            self.sock.connect((self.server_ip, self.port))
            print("Connected")
            d = {"version": self.version, "type": "HELLO", "client_name": self.client_name, "processes": self.processes}
            msg = json.dumps(d) + "\n"
            self.sock.sendall(msg.encode("utf-8"))
            print("Sent")

            msg = self.sock.recv(4096).decode("utf-8")
            while "\n" not in msg:
                msg += self.sock.recv(4096).decode("utf-8")
            first_msg = msg.split("\n")[0]
            d = json.loads(first_msg)
            if d["version"] != self.version: return
            if d["type"] != "WELCOME": return
            self.hash_md5 = d["target_hash"]
            self.servers_name = d["server_name"]


if __name__ == "__main__":
    c = Client()