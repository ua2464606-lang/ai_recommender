import datetime
import os
import pickle
import tempfile
import uuid

import faiss
import numpy as np
from flask import Flask, jsonify, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_database_path() -> str:
    configured_path = os.environ.get("NEURALFIND_DB_PATH")
    if configured_path:
        db_path = os.path.abspath(configured_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return db_path

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        db_path = os.path.join(local_app_data, "NeuralFind", "recommender.db")
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return db_path
        except OSError:
            pass

    db_path = os.path.join(tempfile.gettempdir(), "neuralfind_recommender.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


DB_PATH = get_database_path()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai-recommender-secret-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
db = SQLAlchemy(app)


class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_text = db.Column("query", db.String(500), nullable=False)
    result_count = db.Column(db.Integer, default=0)
    category_filter = db.Column(db.String(100), default="All")
    session_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    url = db.Column(db.String(1000))
    match_score = db.Column(db.Float)
    session_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class RecentlyViewed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100))
    url = db.Column(db.String(1000))
    session_id = db.Column(db.String(100))
    viewed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class RecommendationEngine:
    def __init__(self):
        self.index = None
        self.metadata = None
        self.vectorizer = None
        self._load()

    def _load(self):
        index_path = os.path.join(BASE_DIR, "recommendation.index")
        meta_path = os.path.join(BASE_DIR, "metadata.pkl")

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            print("[Engine] WARNING: index/metadata not found.")
            return

        self.index = faiss.read_index(index_path)
        with open(meta_path, "rb") as f:
            payload = pickle.load(f)

        self.metadata = payload["records"]
        self.vectorizer = payload["vectorizer"]
        print(f"[Engine] Loaded {self.index.ntotal} items.")

    def recommend(self, query: str, top_k: int = 10, category: str = "All") -> list:
        if self.index is None or self.vectorizer is None:
            return []

        vec = self.vectorizer.transform([query]).toarray().astype(np.float32)
        faiss.normalize_L2(vec)

        k = min(top_k * 3, self.index.ntotal)
        scores, indices = self.index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            item = self.metadata[idx]
            item_category = item.get("category", "")
            item_source = item.get("source", "")

            if category != "All" and (
                item_category.lower() != category.lower()
                and item_source.lower() != category.lower()
            ):
                continue

            description = item.get("description", "")
            match_pct = max(round(float(score) * 100, 1), 0.0)

            results.append(
                {
                    "title": item.get("title", ""),
                    "category": item_category,
                    "description": (
                        description[:200] + "..."
                        if len(description) > 200
                        else description
                    ),
                    "tags": item.get("tags", ""),
                    "url": item.get("url", "#"),
                    "match_score": match_pct,
                    "source": item_source,
                }
            )

            if len(results) >= top_k:
                break

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

    def get_category_counts(self) -> dict:
        if not self.metadata:
            return {}

        counts = {}
        for item in self.metadata:
            category = item.get("category", "Unknown")
            counts[category] = counts.get(category, 0) + 1
        return counts


engine = RecommendationEngine()


def get_session_id():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


CATEGORY_ICONS = {
    "All": "bi-stars",
    "Movies": "bi-film",
    "Games": "bi-controller",
    "Courses": "bi-mortarboard",
    "Books": "bi-book",
    "Software": "bi-tools",
}

TRENDING = [
    "Learn Artificial Intelligence",
    "Open world RPG games",
    "Sci-fi movies",
    "Python programming",
    "Cybersecurity tools",
    "Machine learning courses",
    "Fantasy books",
    "Productivity software",
    "Graphic design courses",
    "Data science",
]


@app.route("/")
def index():
    sid = get_session_id()
    category_counts = engine.get_category_counts()
    recent = (
        db.session.query(RecentlyViewed)
        .filter_by(session_id=sid)
        .order_by(RecentlyViewed.viewed_at.desc())
        .limit(5)
        .all()
    )
    fav_count = db.session.query(Favorite).filter_by(session_id=sid).count()

    return render_template(
        "index.html",
        category_counts=category_counts,
        recent=recent,
        fav_count=fav_count,
        trending=TRENDING,
        icons=CATEGORY_ICONS,
    )


@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    top_k = min(int(data.get("top_k", 10)), 20)
    category = data.get("category", "All")
    sid = get_session_id()

    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    results = engine.recommend(query, top_k=top_k, category=category)

    db.session.add(
        SearchHistory(
            search_text=query,
            result_count=len(results),
            category_filter=category,
            session_id=sid,
        )
    )
    db.session.commit()

    return jsonify({"results": results, "query": query, "total": len(results)})


@app.route("/api/favorite", methods=["POST"])
def add_favorite():
    data = request.get_json(silent=True) or {}
    sid = get_session_id()
    title = data.get("title", "").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400

    existing = (
        db.session.query(Favorite).filter_by(title=title, session_id=sid).first()
    )
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"status": "removed"})

    db.session.add(
        Favorite(
            title=title,
            category=data.get("category"),
            description=data.get("description"),
            url=data.get("url"),
            match_score=data.get("match_score"),
            session_id=sid,
        )
    )
    db.session.commit()

    return jsonify({"status": "added"})


@app.route("/api/viewed", methods=["POST"])
def mark_viewed():
    data = request.get_json(silent=True) or {}
    sid = get_session_id()
    title = data.get("title", "").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400

    db.session.add(
        RecentlyViewed(
            title=title,
            category=data.get("category"),
            url=data.get("url"),
            session_id=sid,
        )
    )
    db.session.commit()

    return jsonify({"status": "ok"})


@app.route("/favorites")
def favorites():
    sid = get_session_id()
    favs = (
        db.session.query(Favorite)
        .filter_by(session_id=sid)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return render_template("favorites.html", favorites=favs, icons=CATEGORY_ICONS)


@app.route("/history")
def history():
    sid = get_session_id()
    searches = (
        db.session.query(SearchHistory)
        .filter_by(session_id=sid)
        .order_by(SearchHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template("history.html", searches=searches)


@app.route("/api/stats")
def stats():
    sid = get_session_id()
    total_searches = (
        db.session.query(SearchHistory).filter_by(session_id=sid).count()
    )
    total_favs = db.session.query(Favorite).filter_by(session_id=sid).count()

    top_queries = (
        db.session.query(
            SearchHistory.search_text,
            func.count(SearchHistory.id).label("cnt"),
        )
        .filter_by(session_id=sid)
        .group_by(SearchHistory.search_text)
        .order_by(func.count(SearchHistory.id).desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "total_searches": total_searches,
            "total_favorites": total_favs,
            "top_queries": [{"query": q, "count": c} for q, c in top_queries],
        }
    )


@app.route("/api/trending")
def trending():
    top = (
        db.session.query(
            SearchHistory.search_text,
            func.count(SearchHistory.id).label("cnt"),
        )
        .group_by(SearchHistory.search_text)
        .order_by(func.count(SearchHistory.id).desc())
        .limit(8)
        .all()
    )

    if top:
        return jsonify([{"query": q, "count": c} for q, c in top])
    return jsonify([{"query": t, "count": 0} for t in TRENDING[:8]])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
