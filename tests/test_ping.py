from unittest.mock import patch, MagicMock
from engine.ping import ping_host, tcp_ping

def test_ping_host_returns_dict_keys():
    with patch("engine.ping.ping3.ping", return_value=0.032):
        result = ping_host("8.8.8.8")
    assert "ping_ms" in result
    assert "loss_pct" in result
    assert "method" in result

def test_ping_host_calculates_loss():
    # 1 out of 4 packets lost
    with patch("engine.ping.ping3.ping", side_effect=[0.01, None, 0.01, 0.01]):
        result = ping_host("8.8.8.8", count=4)
    assert result["loss_pct"] == 25.0

def test_ping_host_all_lost():
    with patch("engine.ping.ping3.ping", return_value=None):
        result = ping_host("8.8.8.8", count=4)
    assert result["ping_ms"] is None
    assert result["loss_pct"] == 100.0

def test_tcp_ping_success():
    with patch("engine.ping.socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = MagicMock(return_value=None)
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        result = tcp_ping("github.com", 443)
    assert result["ping_ms"] is not None
    assert result["method"] == "tcp"

def test_tcp_ping_failure():
    with patch("engine.ping.socket.create_connection", side_effect=OSError):
        result = tcp_ping("github.com", 443)
    assert result["ping_ms"] is None
    assert result["loss_pct"] == 100.0
