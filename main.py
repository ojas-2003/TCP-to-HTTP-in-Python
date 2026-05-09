import socket


def send_chunked_post():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 8080))

    request = (
        b"POST /users HTTP/1.1\r\n"
        b"Host: 127.0.0.1:8080\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Content-Type: application/json\r\n"
        b"\r\n"
        b"10\r\n"                       # 0x10 = 16 bytes
        b'{"name": "Ojas"}\r\n'
        b"0\r\n"
        b"\r\n"
    )
    s.sendall(request)

    response = b""
    while True:
        chunk = s.recv(1024)
        if not chunk:
            break
        response += chunk

    print(response.decode())
    s.close()


if __name__ == '__main__':
    send_chunked_post()
