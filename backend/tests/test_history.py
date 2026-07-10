from app.services import history


def _result(before, after, verified=True):
    return {"score": {"before": {"score": before}, "after": {"score": after}}, "verified": verified}


def test_dashboard_groups_by_target():
    history._RING.clear()
    history.record("a@x.com", "refine", "acme/one:README.md", _result(50, 60))
    history.record("a@x.com", "refine", "acme/two:README.md", _result(90, 92))
    history.record("a@x.com", "refine", "acme/one:README.md", _result(60, 70))

    rows = history.dashboard()
    targets = {r["target"] for r in rows}
    assert targets == {"acme/one:README.md", "acme/two:README.md"}
    one = next(r for r in rows if r["target"] == "acme/one:README.md")
    assert one["runs"] == 2
    assert one["latest_score"] == 70
    assert one["trend"] == [60, 70]  # chronological, oldest first


def test_dashboard_sorts_worst_first():
    history._RING.clear()
    history.record("a@x.com", "refine", "acme/high:README.md", _result(80, 95))
    history.record("a@x.com", "refine", "acme/low:README.md", _result(20, 30))

    rows = history.dashboard()
    assert [r["target"] for r in rows] == ["acme/low:README.md", "acme/high:README.md"]


def test_dashboard_target_without_score_sorts_last():
    history._RING.clear()
    history.record("a@x.com", "refine", "acme/blocked:README.md", {"status": "blocked"})
    history.record("a@x.com", "refine", "acme/ok:README.md", _result(10, 20))

    rows = history.dashboard()
    assert rows[-1]["target"] == "acme/blocked:README.md"
    assert rows[-1]["latest_score"] is None


def test_dashboard_empty():
    history._RING.clear()
    assert history.dashboard() == []
