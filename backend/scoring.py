"""
Priority scoring: deliberately a transparent weighted formula, not a black
box model. Policymakers (and hackathon judges) should be able to see why a
district ranked where it did - every input and weight is inspectable.

score = w_demand * demand_norm
      + w_infra   * infra_deficit_score
      + w_urgency * urgency_norm
      + w_scale   * population_norm

All components are normalized to [0, 1] before weighting so no single raw
metric (e.g. population in the millions) dominates by scale alone.
"""

WEIGHTS = {
    "demand": 0.35,
    "infra_deficit": 0.30,
    "urgency": 0.20,
    "population": 0.15,
}


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def rank_districts(hotspots: list[dict], districts_by_id: dict[int, dict]) -> list[dict]:
    """
    hotspots: output of dedup.compute_hotspots()
    districts_by_id: {district_id: {"infra_deficit_score", "population", "planned_budget_cr", "state", "name"}}
    """
    demand_raw = [h["distinct_issues"] for h in hotspots]
    urgency_raw = [
        (h["high_urgency_count"] / h["total_requests"]) if h["total_requests"] else 0
        for h in hotspots
    ]
    infra_raw = [districts_by_id[h["district_id"]]["infra_deficit_score"] for h in hotspots]
    pop_raw = [districts_by_id[h["district_id"]]["population"] for h in hotspots]

    demand_n = _normalize(demand_raw)
    urgency_n = _normalize(urgency_raw)
    infra_n = _normalize(infra_raw)
    pop_n = _normalize(pop_raw)

    ranked = []
    for i, h in enumerate(hotspots):
        d = districts_by_id[h["district_id"]]
        score = (
            WEIGHTS["demand"] * demand_n[i]
            + WEIGHTS["infra_deficit"] * infra_n[i]
            + WEIGHTS["urgency"] * urgency_n[i]
            + WEIGHTS["population"] * pop_n[i]
        )
        ranked.append({
            "district_id": h["district_id"],
            "district_name": h["district_name"],
            "state": d["state"],
            "lat": h["lat"],
            "lon": h["lon"],
            "priority_score": round(score, 4),
            "score_breakdown": {
                "demand": round(WEIGHTS["demand"] * demand_n[i], 4),
                "infra_deficit": round(WEIGHTS["infra_deficit"] * infra_n[i], 4),
                "urgency": round(WEIGHTS["urgency"] * urgency_n[i], 4),
                "population": round(WEIGHTS["population"] * pop_n[i], 4),
            },
            "distinct_issues": h["distinct_issues"],
            "total_requests": h["total_requests"],
            "high_urgency_count": h["high_urgency_count"],
            "planned_budget_cr": d["planned_budget_cr"],
        })

    return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)
