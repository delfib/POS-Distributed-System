import socket


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def send_message(self, message: str) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(message.encode("utf-8"))
            data = s.recv(1024)
            return data.decode("utf-8")


if __name__ == "__main__":
    client = Client("127.0.0.1", 8000)
    response = client.send_message("HELLO")
    print(f"Received: {response}")
