# engine/dns.py
"""
Route all DNS lookups through public resolvers (8.8.8.8 / 1.1.1.1).

Patches socket.getaddrinfo once at startup.  Every downstream call —
requests/urllib3, ping3, socket.create_connection — resolves hostnames
via the public servers automatically, with no changes needed elsewhere.
"""
import socket
import struct
import random

_original_getaddrinfo = socket.getaddrinfo

_SERVERS = ("8.8.8.8", "1.1.1.1")
_TIMEOUT = 3.0

# Session-level cache: hostname → IP string
_cache: dict[str, str] = {}


# ── raw UDP DNS A-query ────────────────────────────────────────────────────────

def _udp_query(hostname: str, server: str) -> str | None:
    """Send a DNS A-record query to server:53. Returns first A-record or None."""
    qid = random.randint(1, 65535)

    # Header: ID | RD=1 | QDCOUNT=1
    pkt = struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0)
    # QNAME
    for label in hostname.encode("ascii").split(b"."):
        pkt += bytes([len(label)]) + label
    pkt += b"\x00"                          # root label
    pkt += struct.pack(">HH", 1, 1)        # QTYPE=A, QCLASS=IN

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(_TIMEOUT)
        try:
            s.sendto(pkt, (server, 53))
            resp, _ = s.recvfrom(512)
        finally:
            s.close()
    except Exception:
        return None

    if len(resp) < 12:
        return None

    r_id, _flags, qdcount, ancount = struct.unpack(">HHHH", resp[:8])
    if r_id != qid or ancount == 0:
        return None

    # Skip header
    pos = 12
    # Skip question section (qdcount entries)
    for _ in range(qdcount):
        while pos < len(resp):
            ln = resp[pos]
            if ln == 0:
                pos += 1
                break
            if ln & 0xC0 == 0xC0:   # pointer
                pos += 2
                break
            pos += ln + 1
        pos += 4                    # QTYPE + QCLASS

    # Scan all answer records for the first A record
    for _ in range(ancount):
        if pos >= len(resp):
            break
        # Skip NAME (pointer or label sequence)
        if resp[pos] & 0xC0 == 0xC0:
            pos += 2
        else:
            while pos < len(resp) and resp[pos] != 0:
                pos += resp[pos] + 1
            pos += 1
        if pos + 10 > len(resp):
            break
        rtype, _rclass, _ttl, rdlen = struct.unpack(">HHIH", resp[pos:pos + 10])
        pos += 10
        if rtype == 1 and rdlen == 4:               # A record → IPv4
            return ".".join(str(b) for b in resp[pos:pos + 4])
        pos += rdlen

    return None


# ── public resolver ────────────────────────────────────────────────────────────

def resolve_public(hostname: str) -> str:
    """
    Resolve hostname using public DNS (8.8.8.8 then 1.1.1.1).
    Returns the IPv4 address string, or the original hostname on failure.
    Results are cached for the lifetime of the process.
    """
    if hostname in _cache:
        return _cache[hostname]

    for server in _SERVERS:
        ip = _udp_query(hostname, server)
        if ip:
            _cache[hostname] = ip
            return ip

    _cache[hostname] = hostname     # cache failures too (avoid repeated queries)
    return hostname


# ── getaddrinfo hook ───────────────────────────────────────────────────────────

def _is_ip(host: str) -> bool:
    for af in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(af, host)
            return True
        except OSError:
            pass
    return False


def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if not _is_ip(host):
        ip = resolve_public(host)
        if ip != host:
            return _original_getaddrinfo(ip, port, family, type, proto, flags)
    return _original_getaddrinfo(host, port, family, type, proto, flags)


def install() -> None:
    """
    Patch socket.getaddrinfo globally to use public DNS.
    Call once at process startup (main.py) before any network I/O.
    """
    socket.getaddrinfo = _patched_getaddrinfo
