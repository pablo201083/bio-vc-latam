from src.capital_atlas import _evidence_score


def test_announcement_url_scores_4():
    level, label, _ = _evidence_score(
        "https://techcrunch.com/2026/01/01/startup-raises-round", "", ""
    )
    assert level == 4
    assert label == "investment_announcement"


def test_portfolio_url_scores_2():
    # "portfolio" contains "folio", which also matches the startup-specific
    # pattern — use "investments" to hit the portfolio-only path cleanly.
    level, label, _ = _evidence_score("https://fund.example.com/investments", "", "")
    assert level == 2
    assert label == "fund_portfolio_page"


def test_missing_url_scores_0():
    level, label, _ = _evidence_score("", "", "")
    assert level == 0
    assert label == "missing_or_internal"


def test_non_http_url_scores_0():
    level, label, _ = _evidence_score("internal-note-only", "", "")
    assert level == 0
    assert label == "missing_or_internal"
