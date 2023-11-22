from server import Server
SVPORT=8888
class ServerApp:
    def __init__(self, server_port):
        server = Server(server_port)

def main():
    try:
        app = ServerApp(SVPORT)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()