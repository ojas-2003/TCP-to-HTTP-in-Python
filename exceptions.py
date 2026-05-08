VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
VALID_VERSIONS = {"HTTP/1.0", "HTTP/1.1"}


class HTTPParseError(Exception):
    """Raise when HTTP request line can not be parsed"""
    pass

class MethodNotAllowedError(HTTPParseError):
    """Raised when HTTP method is not recognized"""
    pass

class UnsupportedVersionError(HTTPParseError):
    """Raised when the HTTP version is not supported."""
    pass

class MalformedRequestLineError(HTTPParseError):
    """Raised when the request line structure is invalid."""
    pass
class MalformedHeaderError(HTTPParseError):
    pass

class MalformedBodtError(HTTPParseError):
    pass


class HTTPResponseError(HTTPParseError):
    pass
