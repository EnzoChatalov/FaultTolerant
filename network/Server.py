import socket, pickle, struct
from threading import Thread

class Server(Thread):
    def __init__(self, host, port, queue):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.queue = queue
    
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen()

        while True:
            conn, _ = s.accept()
            try:
                # Read the 4-byte length prefix
                length_data = conn.recv(4)
                if not length_data:
                    conn.close()
                    continue
                msg_len = struct.unpack("!I", length_data)[0]

                # Read the full message
                data = b""
                while len(data) < msg_len:
                    packet = conn.recv(msg_len - len(data))
                    if not packet:
                        break
                    data += packet

                if len(data) != msg_len:
                    print("[ERROR] Incomplete message received")
                    continue

                message = pickle.loads(data)
                self.queue.put(message)

            except Exception as e:
                print(f"[ERROR] Failed to unpickle message: {e}")
            finally:
                conn.close()

    @staticmethod
    def send(host, port, message):
        data = pickle.dumps(message, protocol=pickle.HIGHEST_PROTOCOL)
        length_prefix = struct.pack("!I", len(data))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            s.sendall(length_prefix + data)
        except ConnectionRefusedError:
            print(f"[WARN] Could not connect to {host}:{port} — node not online yet.")
        except Exception as e:
            print(f"[ERROR] Failed to send to {host}:{port}: {e}")
        finally:
            s.close()