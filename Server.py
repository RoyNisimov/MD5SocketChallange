import socket
import threading
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
        self.end = 10000
        self.port = 50505
        self.increments = 1000
        self.mutex = threading.Lock()
        self.curr = self.start
        self.done = False
        self.number = -1
        self.job_id = 0

        self.hash_md5 = md5(str(random.randint(self.start, self.end)).encode("utf-8")).hexdigest()
        #self.hash_md5 = md5(str(1).encode("utf-8")).hexdigest()
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
            connection_conn = Connection(conn, d["client_name"], d["processes"])
            self.clients.append(connection_conn)
            # Sends the welcome message
            d = {"version": self.version, "type": "WELCOME", "server_name": self.server_name, "algorithm": "md5", "target_hash": self.hash_md5}
            msg = json.dumps(d) + "\n"
            conn.sendall(msg.encode("utf-8"))
            msg = ""
            while True:
                if self.done: return
                while "\n" not in msg:
                    msg += conn.recv(4096).decode("utf-8")
                msg = msg.split("\n")
                current_msg = msg.pop(0)
                msg = "\n".join(msg)
                print(msg)
                self.handle_message(current_msg, connection_conn)


        except Exception as e:
            print(e)

    def send_stop(self):
        d = {"version": self.version, "type": "STOP", "number": self.number}
        msg = json.dumps(d) + "\n"
        for connection_conn in self.clients:
            connection_conn.sock.sendall(msg.encode("utf-8"))
        exit()

    def handle_message(self, current_msg, connection_conn):
        d = json.loads(current_msg)
        if d["version"] != self.version:
            return

        if d["type"] == "REQUEST_WORK":
            if self.done:
                d = {"version": self.version, "type": "WAIT", "retry_after_ms": 1000}
                msg = json.dumps(d) + "\n"
                connection_conn.sock.sendall(msg.encode("utf-8"))
            if not self.done:
                job_id = self.job_id
                self.job_id += 1
                connection_conn.job_id = job_id
                with self.mutex:
                    start = self.start
                    end = self.start + self.increments
                    self.start += self.increments
                    if self.start > self.end: self.done = True
                d = {"version": self.version, "type": "WORK", "job_id": job_id, "start": start, "end": end, "target_hash": self.hash_md5, "lease_seconds": 60}
                msg = json.dumps(d) + "\n"
                connection_conn.sock.sendall(msg.encode("utf-8"))
                print(f"GAVE JOB ({start} - {end})")
        elif d["type"] == "FOUND":
            if md5(str(d["number"]).encode()).hexdigest() == self.hash_md5:
                self.done = True
                self.number = d["number"]
                print(f'NUMBER FOUND {d["number"]}')
                self.send_stop()
        elif d["type"] == "DONE":
            if self.done:
                self.send_stop()
            if not self.done:
                with self.mutex:
                    start = self.start
                    end = self.start + self.increments
                    self.start += self.increments
                    if self.start > self.end: self.done = True
                d = {"version": self.version, "type": "WORK", "job_id": connection_conn.job_id, "start": start, "end": end, "target_hash": self.hash_md5, "lease_seconds": 60}
                msg = json.dumps(d) + "\n"
                connection_conn.sock.sendall(msg.encode("utf-8"))
                print(f"GAVE JOB ({start} - {end})")



if __name__ == "__main__":

    s = Server()


