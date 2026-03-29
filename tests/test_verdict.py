import random
from engine.verdict import score_service, compute_verdict

def test_score_perfect():
    assert score_service(accessible=True, ping_ms=50, loss_pct=0.0) == 1.0

def test_score_high_ping():
    assert score_service(accessible=True, ping_ms=150, loss_pct=0.0) == 0.7

def test_score_minor_loss():
    assert score_service(accessible=True, ping_ms=80, loss_pct=2.0) == 0.7

def test_score_very_high_ping():
    assert score_service(accessible=True, ping_ms=250, loss_pct=0.0) == 0.5

def test_score_inaccessible():
    assert score_service(accessible=False, ping_ms=None, loss_pct=100.0) == 0.0

def test_compute_verdict_perfect():
    services = [
        {"accessible": True, "ping_ms": 30, "loss_pct": 0.0},
        {"accessible": True, "ping_ms": 40, "loss_pct": 0.0},
    ]
    result = compute_verdict(services)
    assert result["score"] == 10.0
    assert result["tier"] == "S"

def test_compute_verdict_empty():
    result = compute_verdict([])
    assert result["score"] == 0.0

def test_verdict_message_in_tier(monkeypatch):
    # monkeypatch random.choice to return first element
    monkeypatch.setattr(random, "choice", lambda lst: lst[0])
    services = [{"accessible": True, "ping_ms": 30, "loss_pct": 0.0}]
    result = compute_verdict(services)
    assert isinstance(result["message"], str)
    assert len(result["message"]) > 0
