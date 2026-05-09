from dataclasses import dataclass
from TCP.server.parser.headers import get_content_type, get_content_length
from exceptions import MalformedBodtError

NO_BODY_METHODS = {"GET", "HEAD", "DELETE", "OPTIONS", "TRACE"}

@dataclass
class Body:
    raw: bytes
    content_type: str

    def is_empty(self):
        return len(self.raw) == 0

    def as_text(self, encoding: str = "utf-8") -> str:
        return self.raw.decode(encoding, errors="replace")

    def as_json(self) -> dict:
        import json
        try:
            return json.loads(self.raw)
        except json.JSONDecodeError as e:
            raise MalformedBodtError(f"Body is not valid JSON: {e}")

    def __len__(self):
        return len(self.raw)

    def __repr__(self):
        preview = self.raw[:50]
        suffix = b"..." if len(self.raw) > 50 else b""
        return f"Body({preview + suffix}, content_type={self.content_type})"

def method_allows_body(method: str) -> bool:
    return method.upper() not in NO_BODY_METHODS


def read_body(
    conn,
    method: str,
    headers,              # Headers object from Chapter 5
    partial_body: bytes,  # bytes already pulled in with headers
) -> Body:
    content_type = get_content_type(headers)
    if not method_allows_body(method):
        return Body(raw=b"", content_type=None)

    transfer_encoding = headers.get("transfer-encoding", "").lower()
    if transfer_encoding == "chunked":
        if partial_body:
            # Inject partial body back into a wrapped reader
            raw = read_chunked_body_with_buffer(conn, partial_body)
        else:
            raw = read_chunked_body(conn)
        return Body(raw=raw, content_type=content_type)

    content_length = get_content_length(headers)
    if content_length == 0:
        return Body(raw=b"", content_type=content_type)

    if content_length < 0:
        raise MalformedBodtError(f"Content-Length cannot be negative: {content_length}")

    body_bytes = partial_body

    while len(body_bytes) < content_length:
        chunk = conn.recv(min(4096, content_length - len(body_bytes)))
        if not chunk:
            raise MalformedBodtError(
                f"Connection closed early. Expected {content_length}, got {len(body_bytes)}"
            )
        body_bytes += chunk

    return Body(raw=body_bytes[:content_length], content_type=content_type)


def validate_body(body: Body) -> Body:
    """
    Validate body contents match the declared Content-Type.
    Logs a warning on mismatch but doesn't reject the request.
    """
    if body.is_empty():
        return body

    if body.content_type == "application/json":
        try:
            body.as_json()
        except MalformedBodtError:
            print(f"[WARN] Content-Type is application/json but body is not valid JSON")

    elif body.content_type == "application/x-www-form-urlencoded":
        try:
            parse_form_body(body.raw)
        except Exception:
            print(f"[WARN] Content-Type is form-urlencoded but body is malformed")

    return body

def parse_form_body(raw: bytes) -> dict:
    """
    Parse application/x-www-form-urlencoded body.
    e.g. b'name=Ojas&age=23' → {'name': 'Ojas', 'age': '23'}
    """
    from urllib.parse import unquote_plus

    result = {}
    text = raw.decode("utf-8", errors="replace")

    for pair in text.split("&"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            result[unquote_plus(key)] = unquote_plus(value)
        elif pair:
            result[unquote_plus(pair)] = ""

    return result

def read_chunk_size(conn, buffer: bytes) -> tuple[int, bytes]:
    """
    Read the hex size line of the next chunk.
    Returns (chunk_size_as_int, remaining_buffer).
    """
    # Read until we find \r\n (end of size line)
    while b"\r\n" not in buffer:
        data = conn.recv(1024)
        if not data:
            raise MalformedBodtError("Connection closed while reading chunk size")
        buffer += data

    # Split off the size line
    size_line, _, buffer = buffer.partition(b"\r\n")

    # Parse hex size — strip any chunk extensions (e.g. '1a;ext=value')
    size_str = size_line.split(b";")[0].strip()

    try:
        chunk_size = int(size_str, 16)   # parse hex string → int
    except ValueError:
        raise MalformedBodtError(f"Invalid chunk size: '{size_line.decode()}'")

    return chunk_size, buffer

def read_chunk_data(conn, chunk_size: int, buffer: bytes) -> tuple[bytes, bytes]:
    """
    Read exactly chunk_size bytes of chunk data plus the trailing \r\n.
    Returns (chunk_data, remaining_buffer).
    """
    # Need chunk_size bytes + 2 bytes for trailing \r\n
    needed = chunk_size + 2

    while len(buffer) < needed:
        data = conn.recv(min(4096, needed - len(buffer)))
        if not data:
            raise MalformedBodtError("Connection closed while reading chunk data")
        buffer += data

    chunk_data = buffer[:chunk_size]
    buffer = buffer[needed:]   # skip chunk_data + \r\n

    return chunk_data, buffer

def read_chunked_body(conn) -> bytes:
    """
    Read a full chunked body from the TCP connection.

    Reads chunks one by one until the zero-length terminator,
    assembles and returns the complete body bytes.
    """
    full_body = b""
    buffer = b""

    while True:
        # 1. Read the chunk size line (hex)
        chunk_size, buffer = read_chunk_size(conn, buffer)

        # 2. Zero size = end of body
        if chunk_size == 0:
            break

        # 3. Read exactly chunk_size bytes
        chunk_data, buffer = read_chunk_data(conn, chunk_size, buffer)
        full_body += chunk_data

        print(f"  [chunk] {chunk_size} bytes: {chunk_data[:30]}{'...' if len(chunk_data) > 30 else ''}")

    return full_body

def read_chunked_body_with_buffer(conn, initial_buffer: bytes) -> bytes:
    """
    Same as read_chunked_body but starts with bytes already in buffer
    (pulled in during header read).
    """
    full_body = b""
    buffer = initial_buffer

    while True:
        chunk_size, buffer = read_chunk_size(conn, buffer)
        if chunk_size == 0:
            break
        chunk_data, buffer = read_chunk_data(conn, chunk_size, buffer)
        full_body += chunk_data
        print(f"  [chunk] {chunk_size} bytes: {chunk_data[:30]}{'...' if len(chunk_data) > 30 else ''}")

    return full_body
