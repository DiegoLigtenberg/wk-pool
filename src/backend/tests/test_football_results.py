from app.football_api import count_card_events, regulation_score


def test_regulation_score_uses_fulltime_after_extra_time() -> None:
    fixture = {
        "goals": {"home": 3, "away": 3},
        "score": {
            "fulltime": {"home": 2, "away": 2},
            "extratime": {"home": 3, "away": 3},
            "penalty": {"home": 4, "away": 3},
        },
        "fixture": {"status": {"short": "PEN"}},
    }

    assert regulation_score(fixture) == (2, 2)


def test_direct_red_excludes_second_yellow_sendoff() -> None:
    events = [
        {"type": "Card", "detail": "Yellow Card", "player": {"id": 1, "name": "Cheddira"}},
        {"type": "Card", "detail": "Yellow Card", "player": {"id": 1, "name": "Cheddira"}},
        {"type": "Card", "detail": "Red Card", "player": {"id": 1, "name": "Cheddira"}},
        {"type": "Card", "detail": "Red Card", "player": {"id": 2, "name": "Direct"}},
    ]

    yellow, direct_red = count_card_events(events)
    assert yellow == 2
    assert direct_red == 1


def test_yellow_red_card_counts_as_yellow_not_direct_red() -> None:
    events = [
        {"type": "Card", "detail": "Yellow Card", "player": {"id": 3, "name": "A"}},
        {"type": "Card", "detail": "Yellow Red Card", "player": {"id": 3, "name": "A"}},
    ]

    yellow, direct_red = count_card_events(events)
    assert yellow == 2
    assert direct_red == 0
