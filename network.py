import socket 
import pickle

class Network:
    def __init__(self, host, is_host=False):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = 5555
        self.addr = (self.host, self.port)
        self.is_host = is_host

        if is_host:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', self.port))
            self.server.listen(1)
            print("Waiting for opponent to connect...")
            self.conn, _ = self.server.accept()
        else: 
            self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            return True
        except:
            return False
        
    def send(self, data):
        try: 
            if self.is_host:
                self.conn.send(pickle.dumps(data))
            else:
                self.client.send(pickle.dumps(data))
            return True
        except socket.error as e:
            print(e)
            return False
        
    def receive(self):
        try:
            if self.is_host:
                # may need to increase or decrease these buffers
                connection = self.conn
            else:
                connection = self.client
            # created a buffer that accumulates chunks of data
            # essentially receives data until an empty string is returned
            data = b''
            while True:
                chunk = connection.recv(1024)
                if not chunk:
                    break
                data += chunk
                if len(chunk) < 1024:
                    break

            if data: 
                return pickle.loads(data)
            return None
        
        except socket.error as e:
            print(e)
            return None