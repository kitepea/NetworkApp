import socket
from threading import Thread
from ftplib import FTP
from messageProtocol import Message, Type, Header
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import os
import json
import time

PORT = 8888

class Client:
    def __init__(self, server_host, server_port, host, port):
        # Assign basic info
        self.server_host = server_host
        self.server_port = server_port
        self.host = host
        self.port = port
        self.register()
    def run(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.host, self.port))
        self.listen_socket.setblocking(1)
        if not os.path.exists("local_files.json"):
            with open("local_files.json", "w") as f:
                f.write("{}")
        with open(".json", "r") as f:
            self.files = json.load(f)
        self.fpt_t = self.FTPServer(self.host)
        self.lis_t = Thread(target=self.listen())
        self.lis_t.start()
    def register(self):
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            raise Exception('CONNECT_SERVER_SOCKET_ERROR when REGISTER')
        while True:
            hostname = ""
            input("Type host name: ", hostname)
            payload = {'hostname': hostname}
            request = Message(Header.REGISTER, Type.REQUEST, payload)
            self.send(request, tmp_sock)

            # Handle server's response
            msg = tmp_sock.recv(2048).decode()
            response = Message(Header.REGISTER, Type.RESPONSE, msg)
            result = response.get_info()['result']
            if result == 'OK':
                self.hostname = hostname
                break
        tmp_sock.close()
        self.run
    def leave(self):
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'CONNECT_SERVER_SOCKET_ERROR'
        payload = {'hostname': self.hostname}
        request = Message(Header.LEAVE, Type.REQUEST, payload)
        self.send(request, tmp_sock)


        #Handle server response
        msg = tmp_sock.recv(2048).decode()
        response = Message(Header.LEAVE, Type.RESPONSE, msg)
        result = response.get_info()['result']
        if(result == 'OK'):
            self.exit()
        else:
            print("Fail to leave!")
    def listen(self):
        self.listen_socket.listen()
        while True:
            try:
                rcv_sock, snd_addr = self.listen_socket.accept()
                new_t = Thread(target=self.reply_conn, args=(rcv_sock, snd_addr))
                new_t.start()
            except OSError:
                break
    def reply_conn(self, rcv_sock, snd_addr):
        try:
            rcv_sock.settimeout(5)
            msg_data = rcv_sock.recv(2048).decode()
            msg = Message(None, None, None, msg_data)
            msg_header = msg.get_header()

            if msg_header == Header.PING and snd_addr[0] == self.server_host:
                self.reply_ping(rcv_sock)
            elif msg_header == Header.DISCOVER and snd_addr[0] == self.server_host:
                self.reply_discover(rcv_sock)
            elif msg_header == Header.RETRIEVE:
                self.reply_retrieve(rcv_sock, msg.get_info())
        except Exception as e:
            print(f"An error occurred when reply connection: {e}")
        finally:
            rcv_sock.close()
        return
    def reply_ping(self, rcv_sock):
        # TODO
        return
    def reply_discover(self, sock):
        response = Message(Header.DISCOVER, Type.RESPONSE, self.files)
        self.send(response, sock)
        return
    def reply_retrieve(self, sock, fName):
        if fName in self.files and os.path.exists(self.files[fName]):
           rs_msg = 'Accept'
        else:
           rs_msg = 'Deny'
        response = Message(Header.RETRIEVE,Type.RESPONSE, rs_msg)
        self.send(response, sock)

    def send(self, msg: Message, sock:socket):
        encoded_msg = json.dumps(msg.get_packet()).encode()
        dest = 'server' if sock.getpeername()[0] == self.server_host else sock.getpeername()[0]
        try:
            sock.sendall(encoded_msg)
            print(f"Succesfull to send a {msg.get_header().name} message to {dest}" )
            return True
        except:
            print(f"Failed to send a {msg.get_header().name} message to {dest}")
            return False

    def fetch(self, fName):

        # Request server
        request = Message(Header.FETCH, Type.REQUEST, fName)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'CONNECT_SERVER_SOCKET_ERROR'
        self.send(request, tmp_sock)


        # Handle server's response
        msg = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        response = Message(None, None, None, msg)
        dest_list = response.get_info()['avail_ips']

        if not dest_list:
            return 'NO_AVAILABLE_HOST'
        return dest_list

    def retrieve(self, fName, host):

        request = Message(Header.RETRIEVE, Type.REQUEST, fName)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_sock.settimeout(5)
        try:
            tmp_sock.connect((host, self.port))
        except:
            return 'UNREACHABLE'

        # If request cannot be sent, return
        if not self.send(request, tmp_sock):
            tmp_sock.close()
            return 'UNREACHABLE'

        # Receive the response
        msg = tmp_sock.recv(2048).decode()
        tmp_sock.close()

        # Process the response
        response = Message(None, None, None, msg)
        result = response.get_info()
        # Check if it accepts or refuses to send the file. If DENIED, try other hosts
        if result == 'Deny send file':
            return result

        # If it has accepted, proceed file transfering using FTP

        # Handle non-existing download directory
        if not os.path.exists("downloads/"):
            os.mkdir("downloads/")

        i = 0
        dest_file = fName
        # Handle duplicate file name
        while os.path.exists("downloads/" + dest_file):
            i += 1
            dest_file = fName + f"({i})"

        # File transfer protocol begins
        ftp = FTP(host)
        ftp.login('admin', 'admin')

        with open("downloads/" + dest_file, 'wb') as f:
            ftp.retrbinary(f'RETR {fName}', f.write)

        ftp.quit()
        # File transfer protocol ends


    def exit(self):
        self.fpt_t.join()
        self.lis_t.join()
        return

    def publish(self, lName, fName):
        # Send publish request
        info = {'fname':fName,'lname':lName}
        request = Message(Header.PUBLISH, Type.REQUEST, info)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'CONNECT_SERVER_SOCKET_ERROR'
        self.send(request, tmp_sock)
        # Receive and handle response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        response = Message(None, None, None, response)
        rs = response.get_info()['result']

        # Publish failed, do not add file to repository
        if rs == "ERROR":
            return rs
        # Pulish success, add file to repository
        self.files[fName] = lName
        with open("local_files.json", "w") as f:
            json.dump(self.files, f, indent=4)
        return rs


    class FTPServer(Thread):
        def __init__(self, host_ip):
            Thread.__init__(self)
            self.host_ip = host_ip
            # Initialize FTP server
            authorizer = DummyAuthorizer()
            self.check_cache(None)
            authorizer.add_user('admin', 'admin', './home', perm='r')
            handler = FTPHandler
            handler.authorizer = authorizer
            handler.banner = "Connection Success"

            self.server = ThreadedFTPServer((self.host_ip, 21), handler)
            self.server.max_cons = 256
            self.server.max_cons_per_ip = 5

        def run(self):
            self.server.serve_forever()

        def exit(self):
            self.server.close_all()

    # FTP server on another thread
