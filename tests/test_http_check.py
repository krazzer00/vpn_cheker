from unittest.mock import patch, MagicMock
from engine.http_check import http_check, ai_region_check

def _mock_response(status_code):
    r = MagicMock()
    r.status_code = status_code
    return r

def test_http_check_accessible():
    with patch("engine.http_check.requests.head", return_value=_mock_response(200)):
        result = http_check("https://github.com")
    assert result["accessible"] is True
    assert result["status_code"] == 200
    assert result["response_ms"] is not None
    assert result["error"] is None

def test_http_check_not_accessible():
    with patch("engine.http_check.requests.head", side_effect=Exception("timeout")):
        result = http_check("https://github.com")
    assert result["accessible"] is False
    assert result["status_code"] is None
    assert result["error"] is not None

def test_ai_region_check_accessible_on_401():
    """401 Unauthorized means the endpoint is reachable — just no API key."""
    with patch("engine.http_check.requests.get", return_value=_mock_response(401)):
        result = ai_region_check("https://api.openai.com/v1/models")
    assert result["region_accessible"] is True
    assert result["error"] is None

def test_ai_region_check_blocked_on_403():
    with patch("engine.http_check.requests.get", return_value=_mock_response(403)):
        result = ai_region_check("https://api.openai.com/v1/models")
    assert result["region_accessible"] is False
    assert result["error"] is None

def test_ai_region_check_blocked_on_timeout():
    with patch("engine.http_check.requests.get", side_effect=Exception("timeout")):
        result = ai_region_check("https://api.openai.com/v1/models")
    assert result["region_accessible"] is False
    assert result["error"] is not None
