from __future__ import annotations

from exceptions import MalformedHeaderError

class Headers:
    def __init__(self):
        self._headers: dict[str, list[str]] = {}

    def add(self, key : str, value : str):
        key = key.strip().lower()
        value = value.strip()
        if key not in self._headers:
            self._headers[key] = []

        self._headers[key].append(value)

    def get(self, key, default = None):
        key = key.strip().lower()
        values = self._headers.get(key)
        if values:
            return values[0]
        return default
    def get_all(self, key):
        key = key.strip().lower()
        return self._headers.get(key, [])

    def __contains__(self, key : str) -> bool:
        return key.lower() in self._headers
    def __repr__(self):
        return f"Headers({self._headers})"
    def to_dict(self) -> dict:
        return {k: v[0] if len(v) == 1 else v for k, v in self._headers.items()}


def parse_header_line(line: str) -> tuple[str, str]:
    if line.startswith((" ", "\t")):
        raise MalformedHeaderError(
            f"Folded headers are not supported: '{line}'"
        )

    if ":" not in line:
        raise MalformedHeaderError(
            f"Header line missing ':' separator: '{line}'"
        )

    key, _, value = line.partition(":")

    if " " in key:
        raise MalformedHeaderError(
            f"Header key must not contain spaces: '{key}'"
        )

    if not key.strip():
        raise MalformedHeaderError(
            f"Header key must not be empty: '{line}'"
        )

    return key.strip(), value.strip()

def parse_headers(head_lines: list[str]) -> Headers:
    headers = Headers()
    for line in head_lines:
        # Skip empty lines (there shouldn't be any mid-headers, but be safe)
        if not line.strip():
            continue
        try:
            key, value = parse_header_line(line)
            headers.add(key, value)
        except MalformedHeaderError as e:
            # Log and skip bad headers rather than crashing the whole request
            print(f"[WARN] Skipping malformed header: {e}")
    return headers

def get_content_length(headers: Headers) -> int:
    raw = headers.get("content-length")
    if raw is None:
        return 0
    try:
        length = int(raw)
        if length < 0:
            raise MalformedHeaderError(
                f"Content-Length must be non-negative, got: {length}"
            )
        return length
    except ValueError:
        raise MalformedHeaderError(
            f"Content-Length is not a valid integer: '{raw}'"
        )

def get_content_type(headers: Headers) -> str | None:
    raw = headers.get("content-type")
    if raw is None:
        return None
    # Strip parameters after semicolon
    return raw.split(";")[0].strip().lower()

def is_keep_alive(headers: Headers, version: str) -> bool:
    connection = headers.get("connection", "").lower()
    if version == "HTTP/1.1":
        return connection != "close"
    else:
        return connection == "keep-alive"
