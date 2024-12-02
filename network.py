import socket 
import pickle

class Network:
    def __init__(self, host, is_host=False):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = 5555
        self.addr = (self.host, self.port)
        self.is_host = is_host
        self.connected = False

        if is_host:
            try:
                # Bind to all available interfaces
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Add this to allow port reuse
                self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server.bind(('', self.port))  # Empty string means all available interfaces
                self.server.listen(1)
                print(f"Server started on {self.host}:{self.port}")
                print("Waiting for opponent to connect...")
                self.conn, self.client_addr = self.server.accept()
                print(f"Client connected from {self.client_addr}")
                self.connected = True
            except socket.error as e:
                print(f"Server setup failed: {e}")
                self.connected = False
        else:
            self.connected = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"Connection failed: {e}")
            return False
        
    def send(self, data):
        try:
            if not self.connected:
                return False
                
            connection = self.conn if self.is_host else self.client
            serialized_data = pickle.dumps(data)
            # Send the length of the data first
            data_length = len(serialized_data)
            connection.send(data_length.to_bytes(4, 'big'))
            # Then send the actual data
            connection.send(serialized_data)
            return True
        except socket.error as e:
            print(f"Send failed: {e}")
            self.connected = False
            return False
        
    def receive(self):
        try:
            if not self.connected:
                return None
                
            connection = self.conn if self.is_host else self.client
            # First receive the length of the incoming data
            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                return None
            data_length = int.from_bytes(data_length_bytes, 'big')
            
            # Then receive the actual data
            # Send data until there is no data to send
            data = b''
            remaining = data_length
            while remaining > 0:
                chunk = connection.recv(min(remaining, 4096))
                if not chunk:
                    return None
                data += chunk
                remaining -= len(chunk)

            return pickle.loads(data)
        
        except socket.error as e:
            print(f"Receive failed: {e}")
            self.connected = False
            return None
        
        except socket.error as e:
            print(e)
            return None
        
    def close(self):
        try:
            if self.is_host:
                self.conn.close()
                self.server.close()
            else:
                self.client.close()
        except:
            pass