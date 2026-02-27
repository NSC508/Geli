"""Ranking algorithm for Geli — binary insertion via pairwise comparison + tier-based scoring."""
import models


# Tier score ranges
TIER_RANGES = {
    "like":    (7.0, 10.0),
    "neutral": (4.0, 7.0),
    "dislike": (1.0, 4.0),
}


def get_comparison_state(tier):
    """Initialize binary search state for a new game being inserted into a tier.
    Returns dict with low, high for the binary search bounds.
    If tier is empty, returns None (no comparison needed).
    """
    tier_count = models.count_games_in_tier(tier)
    if tier_count == 0:
        return None  # First game in tier, just insert at position 1
    return {
        "low": 1,
        "high": tier_count,
    }


def get_comparison_target(tier, low, high):
    """Return the game at the midpoint of [low, high] for the next comparison.
    Returns (mid_position, game_dict).
    """
    mid = (low + high) // 2
    game = models.get_game_at_rank(tier, mid)
    return mid, game


def process_comparison(answer, low, high, mid):
    """Process a 'better' or 'worse' answer and return updated bounds.
    Returns (new_low, new_high, insert_position_or_None).
    - If insert_position is not None, the search is complete.
    """
    if answer == "better":
        # New game is better than mid — search upper half (lower rank numbers = better)
        new_high = mid - 1
    else:
        # New game is worse than mid — search lower half
        new_low = mid + 1

    if answer == "better":
        new_low = low
        if new_high < new_low:
            # Insert at mid (push mid and everything after down)
            return new_low, new_high, mid
        return new_low, new_high, None
    else:
        new_high = high
        if new_low > new_high:
            # Insert after mid
            return new_low, new_high, mid + 1
        return new_low, new_high, None


def insert_game(game_data, tier, position):
    """Insert a game at the given position in the tier, shifting others down."""
    models.shift_ranks_down(tier, position)
    models.add_game(game_data, tier, position)


def calculate_scores(games_list):
    """Calculate scores for all games based on tier-based ranges.

    Scores are only assigned when total games >= 10.
    Within each tier, scores are evenly distributed across the tier's range.
    Rank 1 (best) in a tier gets the max score for that tier.
    """
    total = len(games_list)
    if total < 10:
        return games_list  # No scores yet

    for game in games_list:
        tier = game["tier"]
        score_min, score_max = TIER_RANGES[tier]
        # Get all games in this tier to know count
        tier_games = [g for g in games_list if g["tier"] == tier]
        tier_count = len(tier_games)

        if tier_count == 1:
            # Only game in tier gets midpoint
            game["score"] = round((score_min + score_max) / 2, 1)
        else:
            # Position 1 = best = max score, last position = min score
            rank = game["rank_position"]
            game["score"] = round(
                score_max - ((rank - 1) / (tier_count - 1)) * (score_max - score_min),
                1,
            )

    return games_list
