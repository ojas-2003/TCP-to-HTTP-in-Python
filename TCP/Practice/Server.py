import socket

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allows reusing the port immediately after restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(("127.0.0.1", 8080))
    server.listen(5)
    print("Listening on http://127.0.0.1:8080 ...")

    while True:
        conn, addr = server.accept()
        print(f"\n--- New connection from {addr} ---")

        # Read the stream in chunks
        full_data = b""
        while True:
            chunk = conn.recv(1024)  # read 1024 bytes at a time
            full_data += chunk

            # Stop when we've received the full HTTP request
            # (HTTP headers end with a blank line: \r\n\r\n)
            if b"\r\n\r\n" in full_data:
                break

        print("Raw stream received:")
        print(full_data.decode("utf-8"))

        conn.close()

start_server()
