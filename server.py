import time
import socket
import os
import json
from queue import Queue
from threading import Thread
from messageProtocol import Message, Type, Header

SERVER_TIMEOUT = 5
CLPORT = 1111


class Server:
    def __init__(self, server_port):
        self.server_port = server_port
        # Create dictionary for TCP table
        self.clients = {}
        if not os.path.exists("hostname_file.json") or os.path.getsize("hostname_file.json") == 0:
            with open("hostname_file.json", "w") as fp:
                fp.write("{}")
        with open("hostname_file.json", "r") as f:
            self.hostname_file = json.load(f)
        self.start()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((socket.gethostbyname(socket.gethostname()), self.server_port))
        #
        print(f"Server's running on {socket.gethostbyname(socket.gethostname())}, port: {self.server_port}")
        self.server_socket.listen(5)
        lis_t = Thread(target=self.listen, args=())
        lis_t.start()
        self.command()
    def command(self):
        while True:
            request = input("Enter your request:")
            if request == "ping":
                print(f"Current clients:{self.clients}")
                hostname = input("Chose hostname: ")
                self.ping(hostname)
            elif request == "discover":
                print(f"Current_clients:{self.clients}")
                hostname = input("Chose hostname: ")
                self.discover(hostname)

    def listen(self):
        self.active = True
        while self.active:
            try:
                print("Running ... Waiting for connection")
                client_socket, client_addr = self.server_socket.accept()
                hostname = ""
                for k, v in self.clients.items():
                     if client_addr[0] == v:
                         hostname = k
                         break
                client_t = Thread(target=self.handle_client, args=(client_socket, hostname, client_addr[0]))
                client_t.start()
            except Exception as e:
                raise Exception(e)

    def register(self, client_socket:socket, message, ip):
            hostname = message.get_info()['hostname']
            payload = {'result': 'OK'}
            for k in self.clients.keys():
                if hostname == k:
                    payload['result'] = "DULICATED"
                    break
            print(payload['result'])
            if payload['result'] == 'OK':
                self.clients[hostname] = ip
                self.hostname_file[hostname] = []
                print("Curent clients active: ", self.clients)
            response = Message(Header.REGISTER, Type.RESPONSE, payload)
            self.send(response, client_socket)
    def handle_client(self, client_socket, hostname, ip):
        print("Here")
        try:
            # Listen to message from client
            client_socket.settimeout(SERVER_TIMEOUT)
            message = client_socket.recv(2048).decode()

            # Clients have terminated the connection
            if not message:
                client_socket.close()
            # Clients have asked for request
            else:
                # Retrieve header and type
                message = Message(None, None, None, message)
                message_header = message.get_header()

                # Handle each kind of message
                # REQUEST, REGISTER
                if message_header == Header.REGISTER:
                    self.register(client_socket, message, ip)
                # REQUEST, PUBLISH
                elif message_header == Header.PUBLISH:
                    self.publish(client_socket, hostname, message)
                # REQUEST, FETCH
                elif message_header == Header.FETCH:
                    self.fetch(client_socket, hostname, message)
                # REQUEST, LEAVE
                elif message_header == Header.LEAVE:
                    self.leave(client_socket, hostname)

        except Exception as e:
            print(f"Server request handling error for client {hostname}")
            print(f"Status: {e}")


    def publish(self, client_socket, hostname, message):
        print("call pl")
        info = message.get_info()
        fname = info['fname']
        lname = info['lname']
        print(fname)
        print(lname)
        payload = { 'result': None}
        if fname not in self.hostname_file[hostname]:
            print("1")
            self.hostname_file[hostname].append(fname)
            payload['result'] = 'OK'
            print("2")
            with open("hostname_file.json", "w") as fp:
                json.dump(self.hostname_file, fp, indent=4)
            print("3")
        else:
            print("4")
            payload['result'] = 'DUPLICATE'
        print(payload)
        response_message = Message(Header.PUBLISH, Type.RESPONSE, payload)
        self.send(response_message, client_socket)
        print("sent")
        status = f"Client {hostname}: PUBLISH\n"
        if payload['result'] == 'OK':
            status += f'File name: {fname}\n'
        status += f"Status: {payload['result']}\n"
        return status

    def ping(self, hostname):
        if hostname not in list(self.clients.keys()):
             return  "PING: NOT FOUND THIS CLIENT\n"
        ip = self.clients[hostname]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((ip, CLPORT))
                message = Message(Header.PING, Type.REQUEST, 'PING')
                start_time = time.time()
                self.send(message, client_socket)
                response_message = client_socket.recv(2048).decode()
                end_time = time.time()
                response = Message(None, None, None, response_message)
                RTT = "{:,.8f}".format(end_time - start_time)
                if response_message:
                    print(f"PING OK: {response.get_info()['result']}")
                    print( f"Round-Trip Time: {RTT} (s)\n")
                client_socket.close()
            except Exception as e:
                 print(e)

    def discover(self, hostname):

        if hostname not in list(self.clients.keys()):
            print("DISCOVER: NOT FOUND THIS CLIENT")

        client_ip = self.clients[hostname]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, CLPORT))
                message = Message(Header.DISCOVER, Type.REQUEST, 'DISCOVER')
                start_time = time.time()
                self.send(message, client_socket)
                response_message = client_socket.recv(2048).decode()
                end_time = time.time()
                RTT = "{:,.8f}".format(end_time - start_time)
                file_list = Message(None, None, None, response_message).get_info()["file_list"]
                print(f"DISCOVER OK: {file_list}")
                print(f"Round-Trip Time: {RTT} (s)\n")

            except Exception as e:
                print(e)

    def fetch(self, client_socket, hostname, message):
        fname = message.get_info()["fname"]
        ip_list = self.search(fname, hostname)
        payload = {'fname': fname, 'avail_ips': ip_list}
        response = Message(Header.FETCH, Type.RESPONSE, payload)
        self.send(response, client_socket)
        status = f"Client {hostname}: FETCH\n"
        status += f"File name: {fname}\n"
        status += f"Status: OK\n"
        return status

    def search(self, fname, asking_hostname):
        ip_list = []
        for hostname, file_list in self.hostname_file.items():
            if asking_hostname != hostname  and hostname in list(self.clients.keys()) and fname in file_list:
                ip_list.append(self.clients[hostname])
        return ip_list
    def leave(self, client_socket, hostname):
        self.clients.pop(hostname)
        payload = {'result': 'OK'}
        response = Message(Header.LEAVE, Type.RESPONSE, payload)
        self.send(response, client_socket)
        print(f"{hostname} LEAVE OK")
    def send(self,msg: Message, sock: socket):
        encoded_msg = json.dumps(msg.get_packet()).encode()
        dest = sock.getpeername()[0]
        try:
            sock.sendall(encoded_msg)
            print(f"Succesfull to send a {msg.get_header().name} message to {dest}" )
            return True
        except:
            print(f"Failed to send a {msg.get_header().name} message to {dest}")
            return False


