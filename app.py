"""Geli — Video Game Rating App (Flask application)."""
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from igdb_client import IGDBClient
import models
import ranking

app = Flask(__name__)
app.secret_key = "geli-secret-key-change-in-production"

igdb = IGDBClient("creds.json")


@app.before_request
def ensure_db():
    models.init_db()


# ─── Pages ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Rankings page — show all games stack-ranked with optional scores."""
    games = models.get_all_ranked_games()
    total = len(games)
    show_scores = total >= 10
    if show_scores:
        games = ranking.calculate_scores(games)

    liked = [g for g in games if g["tier"] == "like"]
    neutral = [g for g in games if g["tier"] == "neutral"]
    disliked = [g for g in games if g["tier"] == "dislike"]

    return render_template(
        "index.html",
        all_games=games,
        liked=liked,
        neutral=neutral,
        disliked=disliked,
        total=total,
        show_scores=show_scores,
    )


@app.route("/search")
def search_page():
    """Search page for finding and rating games."""
    return render_template("search.html")


@app.route("/compare")
def compare_page():
    """Pairwise comparison page."""
    state = session.get("compare_state")
    if not state:
        return redirect(url_for("index"))

    game_data = state["game_data"]
    tier = state["tier"]
    low = state["low"]
    high = state["high"]

    mid, target_game = ranking.get_comparison_target(tier, low, high)
    state["mid"] = mid
    session["compare_state"] = state

    tier_count = models.count_games_in_tier(tier)
    # Approximate remaining comparisons (log2-ish)
    import math
    remaining = max(1, int(math.log2(max(high - low + 1, 1))) + 1)

    return render_template(
        "compare.html",
        new_game=game_data,
        existing_game=target_game,
        remaining=remaining,
        tier=tier,
        tier_count=tier_count,
    )


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    """Search IGDB for games."""
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])
    try:
        results = igdb.search_games(q)
        # Mark games that are already ranked
        for g in results:
            g["already_ranked"] = models.game_exists(g["igdb_id"])
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rate", methods=["POST"])
def api_rate():
    """Receive initial Like/Neutral/Dislike rating and start comparison if needed."""
    data = request.get_json()
    game_data = data["game"]
    tier = data["tier"]  # 'like', 'neutral', 'dislike'

    # Check if game already ranked
    if models.game_exists(game_data["igdb_id"]):
        return jsonify({"error": "Game already ranked"}), 400

    # Check if comparison is needed
    comp_state = ranking.get_comparison_state(tier)
    if comp_state is None:
        # First game in tier — insert directly at position 1
        ranking.insert_game(game_data, tier, 1)
        return jsonify({"status": "done", "redirect": url_for("index")})

    # Start comparison session
    session["compare_state"] = {
        "game_data": game_data,
        "tier": tier,
        "low": comp_state["low"],
        "high": comp_state["high"],
        "mid": None,
    }
    return jsonify({"status": "compare", "redirect": url_for("compare_page")})


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Process a comparison answer (better/worse)."""
    state = session.get("compare_state")
    if not state:
        return jsonify({"error": "No active comparison"}), 400

    data = request.get_json()
    answer = data["answer"]  # 'better' or 'worse'

    low = state["low"]
    high = state["high"]
    mid = state["mid"]

    new_low, new_high, insert_pos = ranking.process_comparison(answer, low, high, mid)

    if insert_pos is not None:
        # Binary search complete — insert the game
        ranking.insert_game(state["game_data"], state["tier"], insert_pos)
        session.pop("compare_state", None)
        return jsonify({"status": "done", "redirect": url_for("index")})

    # Continue binary search
    state["low"] = new_low
    state["high"] = new_high
    session["compare_state"] = state
    return jsonify({"status": "compare", "redirect": url_for("compare_page")})


@app.route("/api/remove", methods=["POST"])
def api_remove():
    """Remove a game from rankings."""
    data = request.get_json()
    igdb_id = data["igdb_id"]
    models.remove_game(igdb_id)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    models.init_db()
    app.run(debug=True, port=5000)
