from engine.updater.image_updater import ImageUpdater


def test_schedule_propagates_error_on_failure(monkeypatch):
    updater = ImageUpdater()
    calls = {"consume": 0}

    def fake_consume():
        calls["consume"] += 1
        return True

    class FailingService:
        @staticmethod
        def update_from_context(*, force=False):
            _ = force
            raise RuntimeError("kaputt")

    monkeypatch.setattr(updater, "_consume_run_toggle", fake_consume)
    monkeypatch.setattr(updater, "service", FailingService())

    try:
        updater.schedule()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "kaputt"

    assert calls == {"consume": 1}


