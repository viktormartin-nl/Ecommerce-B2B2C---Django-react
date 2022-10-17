"""requests-like interface for PycURL."""

from __future__ import annotations

import ipaddress
import json
import socket
from io import BytesIO
from urllib.parse import urlencode

import pycurl
from django.conf import settings


class CurlError(Exception):
    def __init__(self, message) -> None:
        self.message = message


class Response(object):
    def __init__(self, status_code: int, content: bytes) -> None:
        self.status_code = status_code
        self.content = content

    def json(self):
        return json.loads(self.content.decode())

    @property
    def text(self) -> str:
        return self.content.decode()


def _opensocket(purpose, curl_address):
    family, socktype, protocol, address = curl_address
    if not settings.INTEGRATIONS_ALLOW_PRIVATE_IPS:
        if ipaddress.ip_address(address[0]).is_private:
            return pycurl.SOCKET_BAD

    return socket.socket(family, socktype, protocol)


def _makeheader(k: str, v: str) -> bytes:
    key_bytes = k.encode()
    value_bytes = v.encode("latin-1")
    return key_bytes + b":" + value_bytes


def request(method: str, url: str, **kwargs) -> Response:
    """Make a HTTP request using pycurl, return a Response object.

    The `method` argument specifies the HTTP verb, and must be
    one of: "get", "post", "put".

    The `url` argument is the target URL.

    Optional keyword arguments:

    `data` is the data structure to be sent in the request body. If `data` is a
    dictionary, it will first be urlencoded and sent as form data, with the
    "Content-Type: application/x-www-form-urlencoded" request header set.
    If `data` is string or bytes, it will be sent as-is.

    Example (form data):

    >>> request("post", "http://example.org", data={"u": "jsmith", "p": "hunter2"})

    Example (raw body, will be sent as UTF8 text):
    >>> request("post", "http://example.org", data="glāžšķūņu rūķīši")

    `headers` is a dictionary of request headers to be sent with the request.
    Example:

    >>> request("post", "http://example.org", headers={"User-Agent": "My-UA"})

    `json` is a data structure to be sent in request body as JSON document. The
    data structure must be serializable with the default JSON serializer (json.dumps).
    The "Content-Type: application/json" request will be added automatically.
    Example:

    >>> request("post", "http://example.org", json={"foo": [1, 2, 3]})

    `timeout` specifies the time limit in seconds for completing the
    entire request. If timeout is exceeded, this function will raise CurlException.
    Example:

    >>> request("get", "http://example.org", timeout=5)

    `params` is a dictionary of query string parameters. If specified, the parameters
    will urlencoded and appended to the target URL. Example:

    >>> request("get", "http://example.org", params={"foo": bar})

    The resulting URL in this case would be http://example.org?foo=bar

    `auth` is a (username, password) tuple for Basic authentication. Example:
    >>> request("get", "http://example.org", auth=("jsmith", "hunter2"))

    Notes:

    If the caller does not specify the User-Agent header, this function
    uses a default "healthchecks.io" value.

    If `INTEGRATIONS_ALLOW_PRIVATE_IPS` is set to `False` in Django settings,
    this function will raise CurlException if the target IP address is from
    a private IP range (127.0.0.1, 192.168.x.x, fe80::, ...).

    This function follows up to three HTTP 302 redirects.

    """

    c = pycurl.Curl()
    c.setopt(pycurl.NOSIGNAL, 1)
    c.setopt(pycurl.PROTOCOLS, pycurl.PROTO_HTTP | pycurl.PROTO_HTTPS)
    c.setopt(pycurl.OPENSOCKETFUNCTION, _opensocket)
    c.setopt(pycurl.FOLLOWLOCATION, True)  # Allow redirects
    c.setopt(pycurl.MAXREDIRS, 3)
    if "timeout" in kwargs:
        c.setopt(pycurl.TIMEOUT, kwargs["timeout"])

    if "params" in kwargs:
        url += "?" + urlencode(kwargs["params"])
    c.setopt(pycurl.URL, url.encode())

    if "auth" in kwargs:
        c.setopt(pycurl.USERPWD, "%s:%s" % kwargs["auth"])

    headers = kwargs.get("headers", {})
    data = kwargs.get("data", "")

    if "json" in kwargs:
        data = json.dumps(kwargs["json"])
        headers["Content-Type"] = "application/json"

    if "User-Agent" not in headers:
        headers["User-Agent"] = "healthchecks.io"

    headers_list = [_makeheader(k, v) for k, v in headers.items()]
    c.setopt(pycurl.HTTPHEADER, headers_list)

    if method in ("post", "put"):
        if isinstance(data, dict):
            c.setopt(pycurl.POSTFIELDS, urlencode(data))

        if isinstance(data, str):
            data = data.encode()

        if isinstance(data, bytes):
            c.setopt(pycurl.UPLOAD, 1)
            c.setopt(pycurl.INFILESIZE, len(data))
            c.setopt(pycurl.READDATA, BytesIO(data))

        c.setopt(pycurl.CUSTOMREQUEST, method.upper())

    buffer = BytesIO()
    c.setopt(pycurl.WRITEDATA, buffer)

    try:
        c.perform()
    except pycurl.error as e:
        errcode = e.args[0]
        if errcode == pycurl.E_OPERATION_TIMEDOUT:
            raise CurlError("Connection timed out")
        elif errcode == pycurl.E_COULDNT_RESOLVE_HOST:
            raise CurlError("Could not resolve host")
        elif errcode == pycurl.E_COULDNT_CONNECT:
            raise CurlError("Connection failed")
        elif errcode == pycurl.E_TOO_MANY_REDIRECTS:
            raise CurlError("Too many redirects")
        elif errcode in (pycurl.E_SSL_CONNECT_ERROR, pycurl.E_PEER_FAILED_VERIFICATION):
            raise CurlError("TLS handshake failed")

        raise CurlError(f"HTTP request failed, code: {errcode}")

    status = c.getinfo(pycurl.RESPONSE_CODE)
    c.close()

    return Response(status, buffer.getvalue())


def post(url: str, data=None, **kwargs):
    return request("post", url, data=data, **kwargs)


def get(url: str, **kwargs):
    return request("get", url, **kwargs)
