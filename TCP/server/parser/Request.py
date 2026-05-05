from dataclasses import dataclass
from urllib.parse import unquote
import socket

from TCP.server.parser.headers import parse_headers, Headers
from exceptions import MalformedRequestLineError, MethodNotAllowedError, UnsupportedVersionError

VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
VALID_VERSIONS = {"HTTP/1.0", "HTTP/1.1"}

@dataclass
class RequestLine:
    method : str
    path : str
    query_params : dict
    fragment : str
    version : str

@dataclass
class HTTPRequest:
    request_line: RequestLine
    headers: Headers
    body: bytes

    def __str__(self):
        rl = self.request_line
        return (
            f"Method:  {rl.method}\n"
            f"Path:    {rl.path}\n"
            f"Query:   {rl.query_params}\n"
            f"Version: {rl.version}\n"
            f"Headers: {self.headers.to_dict()}\n"
            f"Body:    {self.body.decode('utf-8', errors='replace')}"
        )

def parse_path(raw_path: str):
    fragment = ""
    if "#" in raw_path:
        raw_path, fragment = raw_path.split("#", 1)
    path, _, query_string = raw_path.partition("?")
    return unquote(path), query_string, fragment

def parse_query_string(query_string: str) -> dict:
    if not query_string:
        return {}
    params = {}
    for pair in query_string.split("&"):
        key, _, value = pair.partition("=")
        params[unquote(key)] = unquote(value)
    return params

def parse_request_line(line: str) -> RequestLine:
    parts = line.strip().split(" ")
    if len(parts) != 3:
        raise MalformedRequestLineError(f"Bad request line: '{line}'")
    method, raw_path, version = parts

    if method != method.upper():
        raise MalformedRequestLineError(f"Method must be uppercase: '{method}'")
    if method not in VALID_METHODS:
        raise MethodNotAllowedError(f"Unknown method: '{method}'")
    if version not in VALID_VERSIONS:
        raise UnsupportedVersionError(f"Unsupported version: '{version}'")

    path, query_string, fragment = parse_path(raw_path)
    query_params = parse_query_string(query_string)

    return RequestLine(method, path, query_params, fragment, version)

def parse_request(conn) -> HTTPRequest:
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = conn.recv(1024)
        if not chunk:
            break
        raw += chunk
    head_bytes, _, partial_body = raw.partition(b"\r\n\r\n")
    lines = head_bytes.decode("utf-8").split("\r\n")

    request_line = parse_request_line(lines[0])

    headers = parse_headers(lines[1:])

    content_length = int(headers.get("content-length", 0))
    body = partial_body
    while len(body) < content_length:
        chunk = conn.recv(min(1024, content_length - len(body)))
        if not chunk:
            break
        body += chunk
    return HTTPRequest(request_line, headers, body)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 8080))
    server.listen(5)
    print("Listening on http://127.0.0.1:8080 ...\n")

    while True:
        conn, addr = server.accept()
        print(f"--- Connection from {addr} ---")
        try:
            req = parse_request(conn)
            print(req)
        except MalformedRequestLineError as e:
            print(f"400 Bad Request: {e}")
        except MethodNotAllowedError as e:
            print(f"405 Method Not Allowed: {e}")
        except UnsupportedVersionError as e:
            print(f"505 Version Not Supported: {e}")
        finally:
            conn.close()
        print()

start_server()




