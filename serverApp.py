from server import Server
SVPORT=8888
class ServerApp:
    def __init__(self, server_port):
        server = Server(server_port)
    def run(self):
        def run(self):
            while True:
                request = input("Enter your request:")
                if request == "ping":
                    fName = input("")
                    self.server.ping(fName)
                elif request == "discover":
                    self.server.discover()
                else:
                    break
def main():
    app = ServerApp(SVPORT)
    app.run()
if __name__ == "__main__":
    main()