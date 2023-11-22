from client import Client
import socket
SVHOST = '192.168.1.8'
SVPORT = 8888
CLNAME = socket.gethostname()
CLHOST = socket.gethostbyname(CLNAME)
CLPORT = 1111
class ClientApp:
    def __init__(self, server_host, server_port, client_host, client_port):
        client = Client(server_host, server_port, client_host, client_port)
    # def run(self):
         # while True:
         #    request = input("Enter your request:")
         #    if request == "fetch":
         #        fName = input("Type file name that you want:")
         #        self.client.fetch(fName)
         #    elif request == "public":
         #        lName = input("lName=")
         #        fName = input("fName=")
         #        self.client.publish()
         #    elif request == "leave":
         #        self.client.leave()
         #        break

def main():
    try:
        app = ClientApp(SVHOST, SVPORT, CLHOST, CLPORT)
        print("Here")
    except Exception as e:
        print(e)
        return
    # app.run()
if __name__ == "__main__":
    main()