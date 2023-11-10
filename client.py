import socket
from threading import Thread
from ftplib import FTP
from messageProtocol import messageProtocol as MP
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import os
import json
import time

PORT = 8888

class Client:
    def __init__(self, server_host, server_port, host, hostname, port):
        # Assign basic info
        self.server_host = server_host
        self.server_port = server_port
        self.hostname = hostname
        self.host = host
        self.port = port
        self.run()
    def run(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.host, self.port))
        if not os.path.exists("local_files.json"):
            with open("local_files.json", "w") as f:
                f.write("{}")
        with open(".json", "r") as f:
            self.files = json.load(f)
        self.fpt_t = self.FTPServer(self.host)
        self.lis_t = Thread(target=self.listen())
        self.lis_t.start()

    def ftpServer(self):
        return
    def listen(self):
        self.listen_socket.listen()
        while True:
            rcv_sock, snd_addr = self.listen_socket.accept()
            new_t = Thread(target=self.reply_conn, args=(rcv_sock, snd_addr))
            new_t.start()
    def reply_conn(self, rcv_sock, snd_addr):
        try:
            rcv_sock.settimeout(5)
            msg_data = rcv_sock.recv(2048).decode()
            msg = MP(None, None, None, msg_data)
            msg_code = msg.getpCode()

            if msg_code == 10 and snd_addr[0] == self.server_host:
                self.reply_ping(rcv_sock)
            elif msg_code == 11 and snd_addr[0] == self.server_host:
                self.reply_discover(rcv_sock)
            elif msg_code == 12:
                self.reply_fetch(rcv_sock, msg.getfName())
        except Exception as e:
            print(f"An error occurred in listen: {e}")
        finally:
            rcv_sock.close()
        return
    def reply_ping(self, rcv_sock):
        # TODO
        return
    def reply_discover(self, sock):
        response = MP(11, self.files, None)
        self.send(response, sock, 'DISCOVER')
        return
    def reply_fetch(self, sock, fName):
        if fName in self.files and os.path.exists(self.files[fName]):
           rs_msg = 'Accept'
        else:
           rs_msg = 'Deny'
        response = MP(12,None, None, rs_msg)
        self.send(response, sock, 'FETCH')

    def send(self, msg:MP, sock:socket, type):
        encoded_msg = msg.getmsg().encode()
        dest = 'server' if sock.getpeername()[0] == self.server_host else sock.getpeername()[0]
        try:
            sock.sendall(encoded_msg)
            print(f"Succesfull to send a {type} message to {dest}" )
            return True
        except:
            print(f"Failed to send a {type} message to {dest}")

            return False

    def fetch(self, fName):

        # Request server
        request = MP(113, None, fName)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'CONNECT_SERVER_SOCKET_ERROR'
        self.send(request, tmp_sock)


        # Handle server's response
        msg = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        response = MP(None, None, None, msg)
        host_dest = response.getfName()

        if not host_dest:
            return 'NO_AVAILABLE_HOST'

        self.download(fName, host_dest)
    def download(self, fName, host):

        request = MP(113, None, fName)
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
        response = MP(None, None, None, msg)
        result = response.getfName()
        # Check if it accepts or refuses to send the file. If DENIED, try other hosts
        if result == 'DENIED':
            return result

        # If it has accepted, proceed file transfering using FTP
        dest_dir, dest_file = "downloads/", fName
        # Handle non-existing download directory
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        i = 0
        # Handle existing files
        while os.path.exists(dest_dir + dest_file):
            i += 1
            dest_file = fName + f"({i})"

        # File transfer protocol begins
        ftp = FTP(host)
        ftp.login('admin', 'admin')

        with open(dest_dir + dest_file, 'wb') as f:
            ftp.retrbinary(f'RETR {fName}', f.write)

        ftp.quit()
        # File transfer protocol ends


    def exit(self):
        self.fpt_t.join()
        self.lis_t.join()
        return

    def publish(self, lName, fName):
        # Send publish request
        request = MP(1, [fName, lName], None)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'CONNECT_SERVER_SOCKET_ERROR'
        self.send(request, tmp_sock)
        # Receive and handle response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        response = MP(None, None, None, response)
        msg = response.getmsg()

        # Publish failed, do not add file to repository
        if msg == "ERROR":
            return msg
        # Pulish success, add file to repository
        self.files[fName] = lName
        with open("local_files.json", "w") as f:
            json.dump(self.files, f, indent=4)
        return msg


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
