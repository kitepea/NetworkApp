import socket

class Client:
    def __init__(self, server_ip, server_port):
        # Server info:
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #Client info:
        self.client_ip = socket.gethostbyname(socket.gethostname())
        self.client_published_files = []
