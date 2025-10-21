import socket, pickle
from threading import Thread
class Server(Thread):
    def __init__(self, port, queue, host = "localhost"):
        super().__init__(daemon=True)
        self.port = port
        self.queue = queue
        self.host = host
    
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, self.port))
        s.listen()
        while True:
            conn, _ = s.accept()
            data = conn.recv(4096)
            message = pickle.loads(data)
            self.queue.put(message)
            conn.close()

    
    def send(host, port, message):
        data = pickle.dumps(message)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port)) 
        s.sendall(data)