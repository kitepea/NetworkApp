import socket

class Server:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))

        self.server_ip_lookup = {}
        self.server_file_lookup = {}

    def listen(self):
        # Listen the request:
        self.server_socket.listen()
        while True:
            self.client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr} established")

            while True:
                data = self.client_socket.recv(1024)
                print('received {!r}'.format(data))

    def add_file(self, hostname, fname):
        '''
        Register a new file when client publish
        fname: repo file name
        '''
        self.server_file_lookup[hostname].append(fname)

    def add_host(self, hostname, addr):
        self.server_ip_lookup[hostname] = addr
        self.server_file_lookup[hostname] = []

    def ping(self, hostname, timeout):
        # Return if host is live (true) or not (false)
        client_ip = self.server_ip_lookup[hostname]

        if client_ip is None:
            print(f"No Ip address found for {hostname}")
            return False

        self.client_socket.settimeout(timeout)
        try:
            # Kết nối đến máy khách
            # Sử dụng cổng 80 như một ví dụ
            self.client_socket.connect((hostname, 80))
            # Gửi tin nhắn ping
            self.client_socket.send(b"PING")
            # Chờ phản hồi
            response = self.client_socket.recv(1024)
            # Nếu nhận được phản hồi, máy khách đang hoạt động
            if response:
                print("Client is alive")
        except socket.error as e:
            print(f"Something went wrong: {e}")
        finally:
            self.client_socket.close()
