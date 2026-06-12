from app.espn_soccer_api import count_espn_cards, parse_espn_result, teams_match, top_scorer_from_events


def _mexico_event() -> dict[str, object]:
    return {
        "id": "760415",
        "date": "2026-06-11T19:00Z",
        "competitions": [
            {
                "status": {
                    "type": {
                        "state": "post",
                        "completed": True,
                        "shortDetail": "FT",
                    }
                },
                "competitors": [
                    {
                        "homeAway": "home",
                        "score": "2",
                        "team": {"id": "203", "displayName": "Mexico"},
                    },
                    {
                        "homeAway": "away",
                        "score": "0",
                        "team": {"id": "467", "displayName": "South Africa"},
                    },
                ],
                "details": [
                    {
                        "scoringPlay": True,
                        "team": {"id": "203"},
                        "athletesInvolved": [{"id": "233075", "displayName": "Julián Quiñones"}],
                    },
                    {
                        "yellowCard": True,
                        "team": {"id": "467"},
                        "athletesInvolved": [{"id": "256691", "displayName": "Teboho Mokoena"}],
                    },
                    {
                        "yellowCard": True,
                        "team": {"id": "203"},
                        "athletesInvolved": [{"id": "303577", "displayName": "Brian Gutiérrez"}],
                    },
                    {
                        "redCard": True,
                        "team": {"id": "467"},
                        "athletesInvolved": [{"id": "228595", "displayName": "Sphephelo Sithole"}],
                    },
                    {
                        "scoringPlay": True,
                        "team": {"id": "203"},
                        "athletesInvolved": [{"id": "167060", "displayName": "Raúl Jiménez"}],
                    },
                    {
                        "yellowCard": True,
                        "team": {"id": "467"},
                        "athletesInvolved": [{"id": "266125", "displayName": "Nkosinathi Sibisi"}],
                    },
                    {
                        "redCard": True,
                        "team": {"id": "467"},
                        "athletesInvolved": [{"id": "157046", "displayName": "Themba Zwane"}],
                    },
                    {
                        "redCard": True,
                        "team": {"id": "203"},
                        "athletesInvolved": [{"id": "224323", "displayName": "César Montes"}],
                    },
                ],
            }
        ],
    }


def test_teams_match_handles_local_names() -> None:
    event = _mexico_event()
    assert teams_match("Mexico", "South Africa", event)


def test_parse_espn_result_returns_score_and_cards() -> None:
    parsed = parse_espn_result(_mexico_event())
    assert parsed is not None
    assert parsed["score"] == {"home": 2, "away": 0}
    assert parsed["yellowCards"] == 3
    assert parsed["directRedCards"] == 3


def test_count_espn_cards_ignores_second_yellow_sendoff() -> None:
    details = [
        {"yellowCard": True, "athletesInvolved": [{"id": "1", "displayName": "A"}]},
        {"redCard": True, "athletesInvolved": [{"id": "1", "displayName": "A"}]},
        {"redCard": True, "athletesInvolved": [{"id": "2", "displayName": "B"}]},
    ]
    yellow, direct_red = count_espn_cards(details)
    assert yellow == 1
    assert direct_red == 1


def test_top_scorer_from_events_picks_leader() -> None:
    leader = top_scorer_from_events([_mexico_event()])
    assert leader is not None
    assert leader["goals"] == 1
    assert leader["name"] in {"Julián Quiñones", "Raúl Jiménez"}
    assert leader["team"] == "Mexico"
