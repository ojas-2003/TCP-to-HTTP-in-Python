import socket

def udpSocket():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 8081))
    print("UDP server listening...")
    data, addr = server.recvfrom(1024)
    print(f"Received: {data} from {addr}")

udpSocket()



