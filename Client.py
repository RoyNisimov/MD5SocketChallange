import socket
import json
import threading
import time

from md5searcher import MD5Searcher
import multiprocessing

class Client:
    DISCONNECTED = "DISCONNECTED"
    IDLE = "IDLE"
    WAITING = "WAITING"
    WORKING = "WORKING"
    DONE = "DONE"

    def __init__(self):
        self.version = "1"
        self.port = 50505
        self.server_ip = "127.0.0.1"
        self.client_name = "Roy's computer"
        self.servers_name = ""
        self.hash_md5 = ""
        self.start = 0
        self.end = 0
        self.step = 100000
        self.processes = multiprocessing.cpu_count()
        self.buffer = b""
        self.mode = Client.DISCONNECTED
        self.job_id = None
        self.found = -1
        self.dis = False
        self.mutex = threading.Lock()


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

            listening_thread = threading.Thread(target=self.listen_for_server_msg)
            listening_thread.start()

            self.mode = Client.IDLE
            self.ask_for_work()
            while not self.dis and self.found == -1:
                if self.mode == Client.WORKING:
                    w = self.start_work()
                    if w != -1:
                        self.found = w
                        self.give_hash(w)
                        print(w)
                        self.disconnect()
                    else:
                        self.done_searching()

    def done_searching(self):
        d = {
         "version": self.version,
         "type": "DONE",
         "job_id": self.job_id,
         "checked": self.end
        }
        msg = json.dumps(d) + "\n"
        self.sock.sendall(msg.encode())



    def give_hash(self, num):
        d = {"version": self.version, "type": "FOUND",
             "job_id": self.job_id, "number": num,
            "calculated_hash": self.hash_md5
             }
        msg = json.dumps(d) + "\n"
        self.sock.sendall(msg.encode())


    def ask_for_work(self):
        if self.dis: return
        d = {"version": self.version, "type": "REQUEST_WORK"}
        msg = json.dumps(d) + "\n"
        self.sock.sendall(msg.encode("utf-8"))
        print("ASKING")


    def listen_for_server_msg(self):
        msg = ""
        try:
            while True:
                if not self.dis:
                    print(msg)
                    msg += self.sock.recv(4096).decode("utf-8")
                    while "\n" not in msg:
                        msg += self.sock.recv(4096).decode("utf-8")
                    msg = msg.split("\n")
                    self.handle_message(msg.pop(0))
                    msg = "\n".join(msg)

                else:
                    break
        except ConnectionAbortedError:
            self.disconnect()
        except Exception as e:
            print(e)
        finally:
            self.disconnect()

    def handle_message(self, message):
        d = json.loads(message)
        if d["version"] != self.version:
            return
        if d["type"] == "STOP":
            self.disconnect()
        elif d["type"] == "WORK":
            self.job_id = d["job_id"]
            self.start = d["start"]
            self.end = d["end"]
            self.hash_md5 = d["target_hash"]
            self.mode = Client.WORKING
        elif d["type"] == "WAIT":
            self.mode = Client.WAITING
            time.sleep(d["retry_after_ms"])
            if self.mode == Client.WAITING:
                self.ask_for_work()

    def start_work(self):
        self.mode = Client.WORKING
        return MD5Searcher().find_hash(self.hash_md5, self.processes, self.start, self.end)

    def disconnect(self):
        self.dis = True

if __name__ == "__main__":
    c = Client()