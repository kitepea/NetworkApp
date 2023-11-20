import time
import socket
import os
import json
from queue import Queue
from threading import Thread
from messageProtocol import Message, Type, Header

SERVER_TIMEOUT = 2


class Server:
    def __init__(self, server_port):
        self.server_port = server_port
        # Create dictionary for TCP table
        self.clients = {}
        if not os.path.exists("hostname_file.json") or os.path.getsize("hostname_file.json") == 0:
            with open("hostname_file.json", "w") as fp:
                fp.write("{}")
        self.start()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((socket.gethostbyname(
            socket.gethostname()), self.server_port))
        #
        self.server_socket.setblocking(1)  # try setting this to 1
        #
        print(f"Server's running on {socket.gethostbyname(socket.gethostname())}, port: {self.server_port}")
        listen_thread = Thread(target=self.listen, args=())
        listen_thread.start()

    def close(self):
        # LOGOUT ALTERNATIVE FUNCTION
        response_message = Message(Header.LOG_OUT, Type.RESPONSE, 'OK')
        self.send(self.client_socket, response_message)

        self.active_status = False
        if self.server_socket:
            self.server_socket.close()
        self.ip_to_hostname = {}
        self.hostname_to_ip = {}

    def listen(self):

        self.server_socket.listen()
        print("Running ... Waiting for connection")
        # self.active_status = True
        while True:
            try:
                client_socket, client_addr = self.server_socket.accept()
                #add new info client and start thread
                #check whether this ip have existed yet
                hostname = ""

                for k, v in self.clients.items():
                    if client_addr[0] == v:
                        hostname = k
                        break
                if hostname != "":
                    client_t = Thread(target=self.handle_client, args=(client_socket, hostname))
                    client_t.start()
                else:
                    client_t = Thread(target=self.register, args=(client_socket, client_addr[0]))
                    client_t.start()
            except (Exception,):
                break
    def register(self, client_socket, ip):
        try:
            client_socket.settimeout(SERVER_TIMEOUT)
            message = client_socket.recv(1024).decode()
            if not message:
                client_socket.close()
            else:
                message = Message(None, None, None, message)
                message_header = message.get_header()
            if message_header == Header.REGISTER:
                hostname = message.get_info()["hostname"]
                payload = {'result' : 'OK'}
                for k in self.clients.keys():
                    if hostname == k:
                        payload['result'] = "DULICATED"
                        break
                if payload['result'] == 'OK':
                    print("Curent clients active: ",self.clients)
                    self.clients[hostname] = ip
                response = Message(Header.REGISTER, Type.RESPONSE, payload)
                self.send(response, client_socket)
        except Exception as e:
            print(f"Server request handling error for client {ip}\n")
            print(f"Status: {e}\n")

    def handle_client(self, client_socket, hostname):

        try:
            # Listen to message from client
            client_socket.settimeout(SERVER_TIMEOUT)
            message = client_socket.recv(1024).decode()

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

                # REQUEST, PUBLISH
                if message_header == Header.PUBLISH:
                    print(self.publish(client_socket, hostname, message))
                # REQUEST, FETCH
                elif message_header == Header.FETCH:
                    print(self.fetch(client_socket, hostname, message))
                # REQUEST, LEAVE
                elif message_header == Header.LEAVE:
                    print(self.leave(client_socket, hostname))

        except Exception as e:
            print(f"Server request handling error for client {hostname}\n")
            print(f"Status: {e}\n")


    def publish(self, client_socket, hostname, message):

        info = message.get_info()
        fname = info['fname']
        lname = info['lname']
        payload = {'fname': fname, 'lname': lname, 'result': None}
        if fname not in self.hostname_file[hostname]:
            self.hostname_file[hostname].append(fname)
            payload['result'] = 'OK'
            with open("hostname_file.json", "w") as fp:
                json.dump(self.hostname_file, fp, indent=4)
        else:
            payload['result'] = 'DUPLICATE'
        response_message = Message(Header.PUBLISH, Type.RESPONSE, payload)
        self.send(client_socket, response_message)

        status = f"Client {hostname}: PUBLISH\n"
        if payload['result'] == 'OK':
            status += f'File name: {fname}\n'
        status += f"Status: {payload['result']}\n"
        return status

    def ping(self, hostname):

        client_info = f"--Client--: {hostname}\n"
        if hostname in list(self.hostname_list.keys()):
            if hostname in list(self.hostname_to_ip.keys()):
                client_ip = self.hostname_to_ip[hostname]
            else:
                return client_info + "--Status--: NOT LOGIN YET\n"
        else:
            return client_info + "--Status--: NOT REGISTER YET\n"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.PING, Type.REQUEST, 'PING')
                start_time = time.time()
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                end_time = time.time()
                round_trip_time = "{:,.8f}".format(end_time - start_time)
                if response_message:
                    client_info += "--Status--: ALIVE\n"
                    client_info += f"--Round-Trip Time--: {round_trip_time} (s)\n"
                    return client_info
            except Exception as e:
                client_info += f"--Status--: NOT ALIVE\n"
                client_info += f"--Error--: {e}\n"
                return client_info

    def discover(self, hostname):

        client_info = f"--Client--: {hostname}\n"
        if hostname not in list(self.clients.keys()):
            return client_info + "--Status--: NOT REGISTER YET\n"

        client_ip = self.clients[hostname]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.DISCOVER, Type.REQUEST, 'DISCOVER')
                start_time = time.time()
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                end_time = time.time()
                round_trip_time = "{:,.8f}".format(end_time - start_time)
                file_list = Message(
                    None, None, None, response_message).get_info()
                status = "--Status--: SUCCESS\n"
                status += f"--Round-Trip Time: {round_trip_time} (s)\n"
                status += "--File list--:\n"
                for file in list(file_list.keys()):
                    status += str(file) + '\n'
                return client_info + status
            except Exception as e:
                client_info += f"--Status--: FAIL\n"
                client_info += f"--Error--: {e}\n"
                return client_info

    def fetch(self, client_socket, hostname, message):
        fname = message.get_info()
        ip_list = self.search(fname, client_socket.getpeername()[0])
        payload = {'fname': fname, 'avail_ips': ip_list}
        response = Message(Header.FETCH, Type.RESPONSE, payload)
        self.send(client_socket, response)
        status = f"Client {hostname}: FETCH\n"
        status += f"File name: {fname}\n"
        status += f"Status: OK\n"
        return status

    def search(self, fname, asking_ip):
        ip_list = []
        for hostname, file_list in self.hostname_file.items():
            if asking_ip != self.hostname_to_ip[hostname] and fname in file_list:
                # if self.check_active(hostname):
                ip_list.append(self.clients[hostname])
        return ip_list
    def leave(self, client_socket, hostname):
        self.clients.pop(hostname)
        response = Message(Header.LEAVE, Type.RESPONSE, 'OK')
        self.send(client_socket, response)
        return f'{hostname}LEAVE OK'
    def send(msg: Message, sock):
        encoded_msg = json.dumps(msg.get_packet()).encode()
        dest = sock.getpeername()[0]
        try:
            sock.sendall(encoded_msg)
            print(f"Succesfull to send a {msg.get_header().name} message to {dest}" )
            return True
        except:
            print(f"Failed to send a {msg.get_header().name} message to {dest}")
            return False


