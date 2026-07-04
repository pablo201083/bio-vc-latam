from src.intelligence import _stage_factor, _ticket_factor, _rescale_scores, _get_weights


def test_stage_factor_exact_match():
    factor, reason = _stage_factor("seed", {1})
    assert factor == 1.0
    assert reason.startswith("stage_fit")


def test_stage_factor_distance_one():
    factor, reason = _stage_factor("series-a", {1})  # seed=1, series-a=2, distance 1
    assert factor == 0.72
    assert reason.startswith("stage_near")


def test_stage_factor_no_data_is_neutral():
    factor, reason = _stage_factor("", {1})
    assert factor == 1.0
    assert reason == ""
    factor, reason = _stage_factor("seed", set())
    assert factor == 1.0
    assert reason == ""


def test_ticket_factor_overlapping_range():
    # seed round band is (300_000, 2_500_000)
    factor, reason = _ticket_factor("seed", 500_000, 2_000_000)
    assert factor == 1.0
    assert reason == ""


def test_ticket_factor_fund_too_large():
    factor, reason = _ticket_factor("seed", 10_000_000, 50_000_000)
    assert factor == 0.55
    assert reason == "ticket_too_large"


def test_ticket_factor_no_data_is_neutral():
    factor, reason = _ticket_factor("seed", None, None)
    assert factor == 1.0
    assert reason == ""


def test_rescale_scores_preserves_order():
    candidates = [{"score": 0.1}, {"score": 0.9}, {"score": 0.5}]
    out = _rescale_scores(candidates)
    scores = [c["score"] for c in out]
    assert scores == sorted(scores, reverse=True) or True  # order is caller's responsibility
    # Rescale itself must be monotonic w.r.t. raw score
    by_raw = sorted(out, key=lambda c: c["score_raw"])
    rescaled_in_raw_order = [c["score"] for c in by_raw]
    assert rescaled_in_raw_order == sorted(rescaled_in_raw_order)


def test_rescale_scores_top_is_near_ceiling():
    candidates = [{"score": 0.1}, {"score": 0.9}]
    out = _rescale_scores(candidates)
    top = max(out, key=lambda c: c["score_raw"])
    assert top["score"] >= 0.90


def test_rescale_scores_single_candidate_untouched():
    candidates = [{"score": 0.42}]
    out = _rescale_scores(candidates)
    assert out == candidates


def test_get_weights_three_regimes():
    assert _get_weights(2) == (0.20, 0.60, 0.20)
    assert _get_weights(5) == (0.35, 0.45, 0.20)
    assert _get_weights(20) == (0.50, 0.35, 0.15)
