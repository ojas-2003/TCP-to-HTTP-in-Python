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
        # Placeholder — Chapter 8 implements this
        raise NotImplementedError("Chunked encoding will be handled in Chapter 8")

    content_length = get_content_length(headers)
    if content_length == 0:
        return Body(raw=b"", content_type=content_type)

    if content_length < 0:
        raise MalformedBodtError(f"Content-Length cannot be negative: {content_length}")

    body_bytes = partial_body

    while len(body_bytes) < content_length:
        remaining = content_length - len(body_bytes)
        chunk = conn.recv(min(4096, remaining))

        if not chunk:
            raise MalformedBodtError(
                f"Connection closed prematurely. "
                f"Expected {content_length} bytes, got {len(body_bytes)}"
            )
        body_bytes += chunk
        body_bytes = body_bytes[:content_length]

    return Body(raw=body_bytes, content_type=content_type)

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
