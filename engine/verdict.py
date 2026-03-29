import random
from typing import TypedDict

_VERDICTS = {
    "S": [
        "Топчик, всё летает 🚀",
        "Пиздатый VPN, уважаю",
        "Ни одна собака не заблочила, красавчик",
    ],
    "A": [
        "Норм впн, жить можно 👍",
        "Почти идеально, но могло быть лучше",
        "Сойдёт для сельской местности",
    ],
    "B": [
        "Ну такое... 😐",
        "Работает через жопу, но работает",
        "VPN страдает, но держится",
    ],
    "C": [
        "Это провал, Карл 💀",
        "Твой VPN умирает на наших глазах",
        "Роскомнадзор победил, поздравляю",
    ],
    "F": [
        "Это не VPN, это позор семьи 🗑",
        "Братан, ты забыл включить VPN?",
        "Полный пиздец, меняй провайдера",
    ],
}


class VerdictResult(TypedDict):
    score: float
    tier: str
    message: str
    accessible_count: int
    total_count: int


def score_service(accessible: bool, ping_ms: float | None, loss_pct: float | None) -> float:
    if not accessible:
        return 0.0
    if ping_ms is not None and ping_ms > 200:
        return 0.5
    if (ping_ms is not None and ping_ms > 100) or (loss_pct is not None and loss_pct > 0):
        return 0.7
    return 1.0


def compute_verdict(services: list[dict]) -> VerdictResult:
    """
    services: list of {accessible, ping_ms, loss_pct}
    Returns: {score, tier, message, accessible_count, total_count}
    """
    if not services:
        return VerdictResult(
            score=0.0, tier="F", message=random.choice(_VERDICTS["F"]),
            accessible_count=0, total_count=0
        )

    total = len(services)
    points = sum(score_service(s.get("accessible", False), s.get("ping_ms"), s.get("loss_pct"))
                 for s in services)
    score = round((points / total) * 10, 1)
    accessible_count = sum(1 for s in services if s.get("accessible", False))

    if score >= 9:
        tier = "S"
    elif score >= 7:
        tier = "A"
    elif score >= 5:
        tier = "B"
    elif score >= 3:
        tier = "C"
    else:
        tier = "F"

    return VerdictResult(
        score=score,
        tier=tier,
        message=random.choice(_VERDICTS[tier]),
        accessible_count=accessible_count,
        total_count=total,
    )
