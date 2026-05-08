# server/tcp_server.py

import socket

from TCP.server.parser.Request import parse_request
from TCP.server.response import HTTPResponse, send_response
from exceptions import (
    MalformedRequestLineError,
    MethodNotAllowedError,
    UnsupportedVersionError,
    MalformedBodtError,
)


def handle_request(conn, addr):
    """Parse one request and send back a response."""
    print(f"\n--- Connection from {addr} ---")
    try:
        # Parse the incoming request
        req = parse_request(conn)
        print(req)

        # ── Simple Router ──────────────────────────────────
        method = req.request_line.method
        path   = req.request_line.path

        if path == "/" and method == "GET":
            response = HTTPResponse.ok("Welcome to TCP-to-HTTP server!")

        elif path == "/users" and method == "GET":
            users = [{"id": 1, "name": "Ojas"}, {"id": 2, "name": "Alice"}]
            response = HTTPResponse.ok({"users": users})

        elif path == "/users" and method == "POST":
            data = req.body.as_json()
            response = HTTPResponse.created({"message": "User created", "data": data})

        elif path == "/users" and method == "DELETE":
            response = HTTPResponse.method_not_allowed(["GET", "POST"])

        else:
            response = HTTPResponse.not_found(f"Path '{path}' not found")

        # Set Connection header
        response.set_header("Connection", "close")

        # Send the response
        send_response(conn, response)

    # ── Map parse errors to HTTP status codes ──────────────
    except MalformedRequestLineError as e:
        send_response(conn, HTTPResponse.bad_request(str(e)))

    except MethodNotAllowedError as e:
        send_response(conn, HTTPResponse.method_not_allowed(["GET", "POST", "PUT", "DELETE"]))

    except UnsupportedVersionError as e:
        resp = HTTPResponse._make(505, {"error": str(e)}, "application/json")
        send_response(conn, resp)

    except MalformedBodtError as e:
        send_response(conn, HTTPResponse.bad_request(str(e)))

    except Exception as e:
        print(f"[ERROR] Unhandled: {e}")
        send_response(conn, HTTPResponse.internal_server_error())

    finally:
        conn.close()


def start_server(host: str = "127.0.0.1", port: int = 8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"Listening on http://{host}:{port} ...\n")

    while True:
        conn, addr = server.accept()
        handle_request(conn, addr)
        # Note: single-threaded for now — one request at a time

start_server()
