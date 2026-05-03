import socket
from dataclasses import dataclass


@dataclass
class HTTPRequest:
    method : str
    path: str
    query_string: str
    version: str
    headers: dict
    body: bytes

    def __str__(self):
        return (
            f"Method:  {self.method}\n"
            f"Path:    {self.path}\n"
            f"Query:   {self.query_string}\n"
            f"Version: {self.version}\n"
            f"Headers: {self.headers}\n"
            f"Body:    {self.body.decode('utf-8', errors='replace')}"
        )

def receive_raw_request(conn):
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = conn.recv(1024)
        if not chunk:
            break
        raw += chunk
    return raw

def parse_request(conn) -> HTTPRequest:
    raw = receive_raw_request(conn)

    head,_, partial_body = raw.partition(b"\r\n\r\n")
    head = head.decode("utf-8")

    lines = head.split("\r\n")
    method, path_full, version = lines[0].split(" ")
    path, _, query_string = path_full.partition("?")

    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower()] = value

    content_length = int(headers.get("content_length", 0))
    body = partial_body

    while len(body) < content_length:
        remaining = content_length - len(body)
        chunk = conn.recv(min(1024, remaining))
        if not chunk:
            break

        body += chunk
    return HTTPRequest(method, path, query_string, version, headers, body)

def startServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 8080))
    server.listen(5)
    print("Listening on http://127.0.0.1:8080 ...\n")

    while True:
        conn, addr = server.accept()
        print(f"--- Connection from {addr} ---")
        req = parse_request(conn)
        print(req)
        print()
        conn.close()

startServer()



