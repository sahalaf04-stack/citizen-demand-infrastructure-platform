"""
Deduplication: collapse near-duplicate requests (same district + category,
similar text) into clusters so demand strength = number of distinct
underlying issues, not raw complaint count.

Approach: TF-IDF cosine similarity within each (district, category) group.
This is O(n^2) per group which is fine at demo scale (hundreds of requests);
swap for locality-sensitive hashing or an approximate-nearest-neighbour
index (e.g. FAISS) if you scale to millions of requests nationally.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

SIMILARITY_THRESHOLD = 0.35


def assign_clusters(requests: list[dict]) -> dict[int, int]:
    """
    requests: list of {"id": int, "district_id": int, "category": str, "translated_text": str}
    Returns: {request_id: cluster_id}
    """
    groups: dict[tuple, list[dict]] = {}
    for r in requests:
        key = (r["district_id"], r["category"])
        groups.setdefault(key, []).append(r)

    cluster_map = {}
    next_cluster_id = 1

    for key, group in groups.items():
        texts = [g["translated_text"] or "" for g in group]
        if len(texts) == 1:
            cluster_map[group[0]["id"]] = next_cluster_id
            next_cluster_id += 1
            continue

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            tfidf = vectorizer.fit_transform(texts)
            sims = cosine_similarity(tfidf)
        except ValueError:
            # empty vocabulary (e.g. all stopwords) - treat as all distinct
            for g in group:
                cluster_map[g["id"]] = next_cluster_id
                next_cluster_id += 1
            continue

        assigned = [-1] * len(group)
        for i in range(len(group)):
            if assigned[i] != -1:
                continue
            assigned[i] = next_cluster_id
            for j in range(i + 1, len(group)):
                if assigned[j] == -1 and sims[i][j] >= SIMILARITY_THRESHOLD:
                    assigned[j] = next_cluster_id
            next_cluster_id += 1

        for g, cid in zip(group, assigned):
            cluster_map[g["id"]] = cid

    return cluster_map


def compute_hotspots(requests: list[dict]) -> list[dict]:
    """
    Aggregate requests into per-district demand hotspots.
    requests: list of dicts with district_id, district_name, lat, lon, cluster_id, urgency
    """
    by_district: dict[int, dict] = {}
    for r in requests:
        d = by_district.setdefault(r["district_id"], {
            "district_id": r["district_id"],
            "district_name": r["district_name"],
            "lat": r["lat"],
            "lon": r["lon"],
            "clusters": set(),
            "high_urgency_count": 0,
            "total_requests": 0,
        })
        d["clusters"].add(r["cluster_id"])
        d["total_requests"] += 1
        if r["urgency"] == "high":
            d["high_urgency_count"] += 1

    result = []
    for d in by_district.values():
        result.append({
            "district_id": d["district_id"],
            "district_name": d["district_name"],
            "lat": d["lat"],
            "lon": d["lon"],
            "distinct_issues": len(d["clusters"]),
            "total_requests": d["total_requests"],
            "high_urgency_count": d["high_urgency_count"],
        })
    return sorted(result, key=lambda x: x["distinct_issues"], reverse=True)
