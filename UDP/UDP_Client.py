import socket

def udpClient():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(b"Hello UDP", ("127.0.0.1", 8081))
    print("Sent. No idea if it arrived.")
    client.close()

udpClient()
