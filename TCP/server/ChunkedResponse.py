from TCP.server.response import encode_chunk, encode_terminator, STATUS_PHRASES


class ChunkedResponse:
    """
    An HTTP response that sends its body in chunks.
    Useful when body size is unknown upfront.
    """

    def __init__(
        self,
        status_code: int = 200,
        content_type: str = "text/plain",
        extra_headers: dict = None,
        version: str = "HTTP/1.1",
    ):
        self.status_code = status_code
        self.content_type = content_type
        self.extra_headers = extra_headers or {}
        self.version = version

    def build_headers(self) -> bytes:
        """
        Build and return the response head.
        Note: NO Content-Length — we use Transfer-Encoding instead.
        """
        phrase = STATUS_PHRASES.get(self.status_code, "Unknown")
        status_line = f"{self.version} {self.status_code} {phrase}"

        headers = {
            "Content-Type": self.content_type,
            "Transfer-Encoding": "chunked",
            "Connection": "close",
            **self.extra_headers,
        }

        headers_str = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
        head = f"{status_line}\r\n{headers_str}\r\n\r\n"
        return head.encode("utf-8")

    def send_headers(self, conn):
        """Send just the response headers — before any chunks."""
        conn.sendall(self.build_headers())

    def send_chunk(self, conn, data: str or bytes):
        """Send one chunk of data."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        if data:
            conn.sendall(encode_chunk(data))

    def send_end(self, conn):
        """Send the terminating zero-length chunk."""
        conn.sendall(encode_terminator())

    def stream(self, conn, chunks):
        """
        Convenience method — stream an iterable of chunks.

        Usage:
            response.stream(conn, ["Hello", " ", "World"])
        """
        self.send_headers(conn)
        for chunk in chunks:
            self.send_chunk(conn, chunk)
        self.send_end(conn)
