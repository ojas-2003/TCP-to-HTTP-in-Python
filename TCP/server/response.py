import json
from dataclasses import dataclass, field
from exceptions import HTTPResponseError

STATUS_PHRASES = {
    # 1xx Informational
    100: "Continue",
    101: "Switching Protocols",

    # 2xx Success
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",

    # 3xx Redirection
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",

    # 4xx Client Errors
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    409: "Conflict",
    413: "Content Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",

    # 5xx Server Errors
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    505: "HTTP Version Not Supported",
}

@dataclass
class HTTPResponse:
    status_code: int
    headers: dict = field(default_factory=dict)
    version: str = "HTTP/1.1"
    body: bytes = b""

    def set_header(self, key: str, value: str):
        self.headers[key] = value
        return self

    def _build_status_line(self) -> str:
        phrase = STATUS_PHRASES.get(self.status_code, "Unknown")
        return f"{self.version} {self.status_code} {phrase}"

    def _build_headers(self) -> str:
        self.headers["Content-Length"] = str(len(self.body))
        return "\r\n".join(
            f"{key}: {value}"
            for key, value in self.headers.items()
        )

    def to_bytes(self) -> bytes:
        status_line = self._build_status_line()
        headers_str = self._build_headers()
        head = f"{status_line}\r\n{headers_str}\r\n\r\n"
        return head.encode("utf-8") + self.body

    def __str__(self):
        return self.to_bytes().decode("utf-8", errors="replace")

# ── Factory Methods ───────────────────────────────────────

    @classmethod
    def ok(cls, body: str = "", content_type: str = "text/plain") -> "HTTPResponse":
        """200 OK"""
        return cls._make(200, body, content_type)

    @classmethod
    def created(cls, body: str = "", content_type: str = "application/json") -> "HTTPResponse":
        """201 Created"""
        return cls._make(201, body, content_type)

    @classmethod
    def no_content(cls) -> "HTTPResponse":
        """204 No Content — no body"""
        return cls(status_code=204, headers={}, body=b"")

    @classmethod
    def bad_request(cls, message: str = "Bad Request") -> "HTTPResponse":
        """400 Bad Request"""
        return cls._make(400, {"error": message}, "application/json")

    @classmethod
    def not_found(cls, message: str = "Not Found") -> "HTTPResponse":
        """404 Not Found"""
        return cls._make(404, {"error": message}, "application/json")

    @classmethod
    def method_not_allowed(cls, allowed: list[str]) -> "HTTPResponse":
        """405 Method Not Allowed — must include Allow header per spec"""
        resp = cls._make(405, {"error": "Method Not Allowed"}, "application/json")
        resp.set_header("Allow", ", ".join(allowed))
        return resp

    @classmethod
    def internal_server_error(cls, message: str = "Internal Server Error") -> "HTTPResponse":
        """500 Internal Server Error"""
        return cls._make(500, {"error": message}, "application/json")

    @classmethod
    def _make(cls, status: int, body: str , content_type: str) -> "HTTPResponse":
        """Internal helper — serialize body and set Content-Type."""
        if isinstance(body, dict):
            raw = json.dumps(body).encode("utf-8")
            content_type = "application/json"
        elif isinstance(body, str):
            raw = body.encode("utf-8")
        else:
            raw = body

        headers = {"Content-Type": content_type}
        return cls(status_code=status, headers=headers, body=raw)


def send_response(conn, response: HTTPResponse):
    """
    Send an HTTPResponse over a TCP connection.
    Handles partial sends — sendall() loops until all bytes are written.
    """
    try:
        data = response.to_bytes()
        conn.sendall(data)   # sendall() retries until all bytes sent
        print(f"  → {response.status_code} {STATUS_PHRASES.get(response.status_code, '')}"
              f" ({len(data)} bytes)")
    except OSError as e:
        print(f"[ERROR] Failed to send response: {e}")
