"""Ranking algorithm for Geli — binary insertion via pairwise comparison + tier-based scoring."""
import models


# Tier score ranges
TIER_RANGES = {
    "like":    (7.0, 10.0),
    "neutral": (4.0, 7.0),
    "dislike": (1.0, 4.0),
}


def get_comparison_state(media_type, tier):
    """Initialize binary search state for a new item being inserted into a tier.
    Returns dict with low, high for the binary search bounds.
    If tier is empty, returns None (no comparison needed).
    """
    tier_count = models.count_items_in_tier(media_type, tier)
    if tier_count == 0:
        return None  # First item in tier, just insert at position 1
    return {
        "low": 1,
        "high": tier_count,
    }


def get_comparison_target(media_type, tier, low, high):
    """Return the item at the midpoint of [low, high] for the next comparison.
    Returns (mid_position, item_dict).
    """
    mid = (low + high) // 2
    item = models.get_item_at_rank(media_type, tier, mid)
    return mid, item


def process_comparison(answer, low, high, mid):
    """Process a 'better' or 'worse' answer and return updated bounds.
    Returns (new_low, new_high, insert_position_or_None).
    - If insert_position is not None, the search is complete.
    """
    if answer == "better":
        # New item is better than mid — search upper half (lower rank numbers = better)
        new_high = mid - 1
    else:
        # New item is worse than mid — search lower half
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


def insert_item(item_data, media_type, tier, position):
    """Insert an item at the given position in the tier, shifting others down."""
    models.shift_ranks_down(media_type, tier, position)
    models.add_item(item_data, media_type, tier, position)


def calculate_scores(items_list):
    """Calculate scores for all items based on tier-based ranges.

    Scores are only assigned when total items >= 10.
    Within each tier, scores are evenly distributed across the tier's range.
    Rank 1 (best) in a tier gets the max score for that tier.
    """
    total = len(items_list)
    if total < 10:
        return items_list  # No scores yet

    for item in items_list:
        tier = item["tier"]
        score_min, score_max = TIER_RANGES[tier]
        # Get all items in this tier to know count
        tier_items = [i for i in items_list if i["tier"] == tier]
        tier_count = len(tier_items)

        if tier_count == 1:
            # Only item in tier gets midpoint
            item["score"] = round((score_min + score_max) / 2, 1)
        else:
            # Position 1 = best = max score, last position = min score
            rank = item["rank_position"]
            item["score"] = round(
                score_max - ((rank - 1) / (tier_count - 1)) * (score_max - score_min),
                1,
            )

    return items_list
