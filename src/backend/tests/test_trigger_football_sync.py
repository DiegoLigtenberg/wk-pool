import scripts.trigger_football_sync as trigger


def test_trigger_refuses_to_run_outside_railway(monkeypatch) -> None:
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY_SERVICE_NAME", raising=False)

    assert trigger.main([]) == 1
