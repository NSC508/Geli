"""TMDB API client for Movies and TV Shows."""
import json
import os
import requests


class TMDBClient:
    API_BASE = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p/w300"

    def __init__(self, creds_path="creds.json"):
        # Prefer environment variable; fall back to creds.json
        self.api_key = os.environ.get("TMDB_API_KEY")

        if not self.api_key:
            try:
                with open(creds_path) as f:
                    creds = json.load(f)
                self.api_key = creds.get("tmdb_api_key")
            except FileNotFoundError:
                pass

        if not self.api_key:
            raise RuntimeError(
                "TMDB API key not found. Set TMDB_API_KEY environment variable, "
                "or add 'tmdb_api_key' to your creds.json file. See README for details."
            )

        self._genre_cache_movie = {}
        self._genre_cache_tv = {}

    def _get(self, endpoint, params=None):
        """Make a GET request to the TMDB API."""
        url = f"{self.API_BASE}/{endpoint}"
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _load_genres(self, media):
        """Load and cache genre ID → name mapping."""
        cache = self._genre_cache_movie if media == "movie" else self._genre_cache_tv
        if cache:
            return cache
        data = self._get(f"genre/{media}/list")
        mapping = {g["id"]: g["name"] for g in data.get("genres", [])}
        if media == "movie":
            self._genre_cache_movie = mapping
        else:
            self._genre_cache_tv = mapping
        return mapping

    def _genre_names(self, genre_ids, media):
        """Convert list of genre IDs to comma-separated names."""
        mapping = self._load_genres(media)
        return ", ".join(mapping.get(gid, "") for gid in genre_ids if mapping.get(gid))

    # ── Movies ────────────────────────────────────────────────────

    def search_movies(self, query, limit=20):
        """Search TMDB for movies. Returns list of movie dicts."""
        data = self._get("search/movie", {"query": query})
        results = data.get("results", [])[:limit]

        movies = []
        for m in results:
            release_year = None
            rd = m.get("release_date", "")
            if rd and len(rd) >= 4:
                release_year = int(rd[:4])

            movies.append({
                "external_id": m["id"],
                "name": m.get("title", "Unknown"),
                "cover_url": f"{self.IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
                "release_year": release_year,
                "meta_line": self._genre_names(m.get("genre_ids", []), "movie"),
                "genres": self._genre_names(m.get("genre_ids", []), "movie"),
                "summary": m.get("overview", ""),
            })
        return movies

    def get_movie_by_id(self, movie_id):
        """Fetch a single movie by TMDB ID."""
        try:
            m = self._get(f"movie/{movie_id}")
        except Exception:
            return None

        release_year = None
        rd = m.get("release_date", "")
        if rd and len(rd) >= 4:
            release_year = int(rd[:4])

        genres = ", ".join(g["name"] for g in m.get("genres", []))

        return {
            "external_id": m["id"],
            "name": m.get("title", "Unknown"),
            "cover_url": f"{self.IMAGE_BASE}{m['poster_path']}" if m.get("poster_path") else None,
            "release_year": release_year,
            "meta_line": genres,
            "genres": genres,
            "summary": m.get("overview", ""),
        }

    # ── TV Shows ──────────────────────────────────────────────────

    def search_tv(self, query, limit=20):
        """Search TMDB for TV shows. Returns list of show dicts."""
        data = self._get("search/tv", {"query": query})
        results = data.get("results", [])[:limit]

        shows = []
        for s in results:
            release_year = None
            rd = s.get("first_air_date", "")
            if rd and len(rd) >= 4:
                release_year = int(rd[:4])

            shows.append({
                "external_id": s["id"],
                "name": s.get("name", "Unknown"),
                "cover_url": f"{self.IMAGE_BASE}{s['poster_path']}" if s.get("poster_path") else None,
                "release_year": release_year,
                "meta_line": self._genre_names(s.get("genre_ids", []), "tv"),
                "genres": self._genre_names(s.get("genre_ids", []), "tv"),
                "summary": s.get("overview", ""),
            })
        return shows

    def get_tv_by_id(self, tv_id):
        """Fetch a single TV show by TMDB ID."""
        try:
            s = self._get(f"tv/{tv_id}")
        except Exception:
            return None

        release_year = None
        rd = s.get("first_air_date", "")
        if rd and len(rd) >= 4:
            release_year = int(rd[:4])

        genres = ", ".join(g["name"] for g in s.get("genres", []))

        return {
            "external_id": s["id"],
            "name": s.get("name", "Unknown"),
            "cover_url": f"{self.IMAGE_BASE}{s['poster_path']}" if s.get("poster_path") else None,
            "release_year": release_year,
            "meta_line": genres,
            "genres": genres,
            "summary": s.get("overview", ""),
        }
