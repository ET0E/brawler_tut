import socket 
import pickle
import time
import threading

class Network:
    def __init__(self, host, is_host=False):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = 5555
        self.addr = (self.host, self.port)
        self.is_host = is_host
        self.connected = False
        
        # Add buffers for smoothing
        self.last_received_data = None
        self.send_rate = 1/60  # Send 60 times per second
        self.last_send_time = 0
        
        # Add interpolation values
        self.interpolation_offset = 100  # ms
        self.last_position = None
        self.target_position = None

        if is_host:
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Set TCP_NODELAY to reduce latency
                self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.server.bind(('0.0.0.0', self.port))
                self.server.listen(1)
                print(f"Server listening on {socket.gethostbyname(socket.gethostname())}:{self.port}")
                self.conn, self.client_addr = self.server.accept()
                self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.connected = True
                
                # Start receive thread
                self.receive_thread = threading.Thread(target=self._receive_loop)
                self.receive_thread.daemon = True
                self.receive_thread.start()
                
            except socket.error as e:
                print(f"Server setup failed: {str(e)}")
                self.connected = False
        else:
            self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.connected = self.connect()
            if self.connected:
                # Start receive thread
                self.receive_thread = threading.Thread(target=self._receive_loop)
                self.receive_thread.daemon = True
                self.receive_thread.start()

    def connect(self):
        try:
            self.client.connect(self.addr)
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"Connection failed: {e}")
            return False
        
    def send(self, data):
        current_time = time.time()
        
        # Rate limit sending
        if current_time - self.last_send_time < self.send_rate:
            return True
            
        try:
            if not self.connected:
                return False
                
            # Optimize data before sending
            optimized_data = self._optimize_data(data)
            
            connection = self.conn if self.is_host else self.client
            serialized_data = pickle.dumps(optimized_data)
            
            # Send in a single packet
            message = len(serialized_data).to_bytes(4, 'big') + serialized_data
            connection.sendall(message)
            
            self.last_send_time = current_time
            return True
            
        except socket.error as e:
            print(f"Send failed: {e}")
            self.connected = False
            return False
        
    def _optimize_data(self, data):
        # Only send data that has changed
        if self.last_received_data == data:
            return None
            
        # Round floating point numbers to reduce packet size
        optimized = {}
        for key, value in data.items():
            if isinstance(value, float):
                optimized[key] = round(value, 2)
            else:
                optimized[key] = value
                
        return optimized

        
    def _receive_loop(self):
        while self.connected:
            try:
                data = self._receive_data()
                if data:
                    self.last_received_data = data
            except:
                self.connected = False
                break
            
    def _receive_data(self):
        connection = self.conn if self.is_host else self.client
        
        try:
            # Receive length
            data_length_bytes = connection.recv(4)
            if not data_length_bytes:
                return None
            data_length = int.from_bytes(data_length_bytes, 'big')
            
            # Receive data
            data = connection.recv(data_length)
            if not data:
                return None
                
            return pickle.loads(data)
            
        except socket.error as e:
            print(f"Receive failed: {e}")
            return None
        
    def get_latest_data(self):
        return self.last_received_data
        
    def close(self):
        try:
            if self.is_host:
                self.conn.close()
                self.server.close()
            else:
                self.client.close()
        except:
            pass