"""Geli — Multi-Media Rating App (Flask application)."""
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from igdb_client import IGDBClient
from openlibrary_client import OpenLibraryClient
from tmdb_client import TMDBClient
import models
import ranking

app = Flask(__name__)
app.secret_key = "geli-secret-key-change-in-production"

VALID_MEDIA_TYPES = {"games", "books", "movies", "tv"}

MEDIA_CONFIG = {
    "games":  {"label": "Games",    "singular": "Game",     "emoji": "🎮", "search_hint": "Search for a video game..."},
    "books":  {"label": "Books",    "singular": "Book",     "emoji": "📚", "search_hint": "Search for a book..."},
    "movies": {"label": "Movies",   "singular": "Movie",    "emoji": "🎬", "search_hint": "Search for a movie..."},
    "tv":     {"label": "TV Shows", "singular": "TV Show",  "emoji": "📺", "search_hint": "Search for a TV show..."},
}

# ─── Lazy-init API clients ──────────────────────────────────────────────────
_clients = {}


def get_client(media_type):
    """Get or create the appropriate API client for the media type."""
    if media_type not in _clients:
        if media_type == "games":
            _clients[media_type] = IGDBClient("creds.json")
        elif media_type == "books":
            _clients[media_type] = OpenLibraryClient()
        elif media_type in ("movies", "tv"):
            _clients[media_type] = TMDBClient("creds.json")
    return _clients[media_type]


@app.before_request
def ensure_db():
    models.init_db()


# ─── Root redirect ───────────────────────────────────────────────────────────

@app.route("/")
def root():
    return redirect(url_for("index", media_type="games"))


# ─── Pages ───────────────────────────────────────────────────────────────────

@app.route("/<media_type>/")
def index(media_type):
    """Rankings page — show all items stack-ranked with optional scores."""
    if media_type not in VALID_MEDIA_TYPES:
        return redirect(url_for("index", media_type="games"))

    items = models.get_all_ranked_items(media_type)
    total = len(items)
    show_scores = total >= 10
    if show_scores:
        items = ranking.calculate_scores(items)

    liked = [i for i in items if i["tier"] == "like"]
    neutral = [i for i in items if i["tier"] == "neutral"]
    disliked = [i for i in items if i["tier"] == "dislike"]

    config = MEDIA_CONFIG[media_type]

    return render_template(
        "index.html",
        all_items=items,
        liked=liked,
        neutral=neutral,
        disliked=disliked,
        total=total,
        show_scores=show_scores,
        media_type=media_type,
        media_config=config,
        all_media=MEDIA_CONFIG,
    )


@app.route("/<media_type>/search")
def search_page(media_type):
    """Search page for finding and rating items."""
    if media_type not in VALID_MEDIA_TYPES:
        return redirect(url_for("index", media_type="games"))

    config = MEDIA_CONFIG[media_type]
    return render_template(
        "search.html",
        media_type=media_type,
        media_config=config,
        all_media=MEDIA_CONFIG,
    )


@app.route("/<media_type>/compare")
def compare_page(media_type):
    """Pairwise comparison page."""
    if media_type not in VALID_MEDIA_TYPES:
        return redirect(url_for("index", media_type="games"))

    state = session.get("compare_state")
    if not state or state.get("media_type") != media_type:
        return redirect(url_for("index", media_type=media_type))

    item_data = state["item_data"]
    tier = state["tier"]
    low = state["low"]
    high = state["high"]

    mid, target_item = ranking.get_comparison_target(media_type, tier, low, high)
    state["mid"] = mid
    session["compare_state"] = state

    tier_count = models.count_items_in_tier(media_type, tier)
    import math
    remaining = max(1, int(math.log2(max(high - low + 1, 1))) + 1)

    config = MEDIA_CONFIG[media_type]

    return render_template(
        "compare.html",
        new_item=item_data,
        existing_item=target_item,
        remaining=remaining,
        tier=tier,
        tier_count=tier_count,
        media_type=media_type,
        media_config=config,
        all_media=MEDIA_CONFIG,
    )


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.route("/<media_type>/api/search")
def api_search(media_type):
    """Search for items."""
    if media_type not in VALID_MEDIA_TYPES:
        return jsonify({"error": "Invalid media type"}), 400

    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])

    try:
        client = get_client(media_type)
        if media_type == "games":
            results = client.search_games(q)
            # Normalize game results to use external_id
            for g in results:
                g["external_id"] = g.pop("igdb_id", g.get("external_id"))
                # Map platforms → meta_line for consistency
                if "platforms" in g and "meta_line" not in g:
                    g["meta_line"] = g["platforms"]
        elif media_type == "books":
            results = client.search_books(q)
        elif media_type == "movies":
            results = client.search_movies(q)
        elif media_type == "tv":
            results = client.search_tv(q)
        else:
            results = []

        # Mark items that are already ranked
        for item in results:
            item["already_ranked"] = models.item_exists(media_type, item["external_id"])

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/<media_type>/api/rate", methods=["POST"])
def api_rate(media_type):
    """Receive initial Like/Neutral/Dislike rating and start comparison if needed."""
    if media_type not in VALID_MEDIA_TYPES:
        return jsonify({"error": "Invalid media type"}), 400

    data = request.get_json()
    item_data = data["item"]
    tier = data["tier"]

    # Check if item already ranked
    if models.item_exists(media_type, item_data["external_id"]):
        return jsonify({"error": "Already ranked"}), 400

    # Check if comparison is needed
    comp_state = ranking.get_comparison_state(media_type, tier)
    if comp_state is None:
        # First item in tier — insert directly at position 1
        ranking.insert_item(item_data, media_type, tier, 1)
        return jsonify({"status": "done", "redirect": url_for("index", media_type=media_type)})

    # Start comparison session
    session["compare_state"] = {
        "item_data": item_data,
        "media_type": media_type,
        "tier": tier,
        "low": comp_state["low"],
        "high": comp_state["high"],
        "mid": None,
    }
    return jsonify({"status": "compare", "redirect": url_for("compare_page", media_type=media_type)})


@app.route("/<media_type>/api/compare", methods=["POST"])
def api_compare(media_type):
    """Process a comparison answer (better/worse)."""
    state = session.get("compare_state")
    if not state or state.get("media_type") != media_type:
        return jsonify({"error": "No active comparison"}), 400

    data = request.get_json()
    answer = data["answer"]

    low = state["low"]
    high = state["high"]
    mid = state["mid"]

    new_low, new_high, insert_pos = ranking.process_comparison(answer, low, high, mid)

    if insert_pos is not None:
        ranking.insert_item(state["item_data"], media_type, state["tier"], insert_pos)
        session.pop("compare_state", None)
        return jsonify({"status": "done", "redirect": url_for("index", media_type=media_type)})

    state["low"] = new_low
    state["high"] = new_high
    session["compare_state"] = state
    return jsonify({"status": "compare", "redirect": url_for("compare_page", media_type=media_type)})


@app.route("/<media_type>/api/remove", methods=["POST"])
def api_remove(media_type):
    """Remove an item from rankings."""
    if media_type not in VALID_MEDIA_TYPES:
        return jsonify({"error": "Invalid media type"}), 400

    data = request.get_json()
    external_id = data["external_id"]
    models.remove_item(media_type, external_id)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    models.init_db()
    app.run(debug=True, port=5000)
