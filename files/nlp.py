"""
services/nlp.py — TF-IDF based menu search
"""

import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import get_db


def find_dishes(query: str, venue_id: str, top_k: int = 5) -> list[dict]:
    """
    Return up to *top_k* menu items whose name / description / tags best
    match *query* using a TF-IDF cosine similarity ranking.
    """
    db   = get_db()
    rows = db.execute(
        "SELECT id, name, description, price, is_veg, is_vegan, tags "
        "FROM menu_items WHERE venue_id=? AND is_available=1",
        (venue_id,),
    ).fetchall()

    if not rows:
        return []

    corpus = [
        f"{r['name']} {r['description']} {' '.join(json.loads(r['tags']))}"
        for r in rows
    ]

    try:
        tfidf  = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = tfidf.fit_transform(corpus + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1])[0]
    except Exception:
        scores = np.zeros(len(rows))

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        {
            "id":          rows[i]["id"],
            "name":        rows[i]["name"],
            "description": rows[i]["description"],
            "price":       rows[i]["price"],
            "is_veg":      bool(rows[i]["is_veg"]),
            "is_vegan":    bool(rows[i]["is_vegan"]),
            "tags":        json.loads(rows[i]["tags"]),
            "score":       round(float(score), 3),
        }
        for i, score in ranked
        if score > 0.01
    ]
