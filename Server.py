import socket
from threading import Lock, Thread
import random
from hashlib import md5
import json

from Connection import Connection

class Server:

    def __init__(self):
        self.version = "1"
        self.server_name = "Roy's server"
        self.clients = []
        self.start = 0
        self.end = 1000000
        self.port = 50505
        self.increments = 100000
        self.curr = self.start
        self.message_buffer = b""

        self.hash_md5 = md5(str(random.randint(self.start, self.end)).encode("utf-8")).hexdigest()
        print(self.hash_md5)
        self.begin_searching()

    def begin_searching(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
                self.sock.bind(("0.0.0.0", self.port))
                self.sock.listen()
                print("Server is up and listening on port ", self.port)
                while True:
                    try:
                        conn, address = self.sock.accept()
                        print("Client connected from ", address)
                        client_thread = Thread(target=self.handle_client, args=[conn, address])
                        client_thread.start()
                    except Exception as e:
                        print(e)
                        try:
                            conn.close()
                        except Exception as e:
                            print(e)
        except Exception as e:
            print(e)
        finally:
            print("end")

    def handle_client(self, conn: socket.socket, address):
        try:
            # Gets the Hello message
            msg = conn.recv(4096).decode("utf-8")
            while "\n" not in msg:
                msg += conn.recv(4096).decode("utf-8")
            first_msg = msg.split("\n")[0]
            d = json.loads(first_msg)
            if d["version"] != self.version:
                print("returning")
                return
            if d["type"] != "HELLO":
                print("returning 2")
                return
            self.clients.append(Connection(conn, d["client_name"], d["processes"]))
            # Sends the welcome message
            d = {"version": self.version, "type": "WELCOME", "server_name": self.server_name, "algorithm": "md5", "target_hash": self.hash_md5}
            msg = json.dumps(d) + "\n"
            conn.sendall(msg.encode("utf-8"))

        except Exception as e:
            print(e)



if __name__ == "__main__":

    s = Server()


