"""IGDB API client with automatic Twitch OAuth token management."""
import json
import os
import time
import requests


class IGDBClient:
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    API_BASE = "https://api.igdb.com/v4"

    def __init__(self, creds_path="creds.json"):
        # Prefer environment variables; fall back to creds.json
        self.client_id = os.environ.get("IGDB_CLIENT_ID")
        self.client_secret = os.environ.get("IGDB_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            try:
                with open(creds_path) as f:
                    creds = json.load(f)
                self.client_id = creds["client_id"]
                self.client_secret = creds["client_secret"]
            except FileNotFoundError:
                raise RuntimeError(
                    "IGDB credentials not found. Set IGDB_CLIENT_ID and "
                    "IGDB_CLIENT_SECRET environment variables, or create a "
                    "creds.json file. See README for details."
                )

        self.access_token = None
        self.token_expires_at = 0

    def _get_token(self):
        """Fetch a new access token from Twitch."""
        resp = requests.post(self.TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        })
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Failed to get IGDB token: {data}")
        self.access_token = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"] - 60

    def _headers(self):
        if not self.access_token or time.time() >= self.token_expires_at:
            self._get_token()
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }

    def _request(self, endpoint, query):
        """Make an IGDB API request with automatic token refresh on 401."""
        url = f"{self.API_BASE}/{endpoint}"
        resp = requests.post(url, headers=self._headers(), data=query)
        if resp.status_code == 401:
            self._get_token()
            resp = requests.post(url, headers=self._headers(), data=query)
        resp.raise_for_status()
        return resp.json()

    def search_games(self, query, limit=20):
        """Search for games by name. Returns list of game dicts."""
        body = (
            f"fields id, name, cover.image_id, first_release_date,"
            f" platforms.abbreviation, genres.name, summary;"
            f' search "{query}";'
            f" limit {limit};"
        )
        results = self._request("games", body)
        games = []
        for g in results:
            cover_id = None
            if "cover" in g and "image_id" in g["cover"]:
                cover_id = g["cover"]["image_id"]
            release_year = None
            if "first_release_date" in g:
                release_year = time.gmtime(g["first_release_date"]).tm_year
            platforms = []
            if "platforms" in g:
                platforms = [p.get("abbreviation", "?") for p in g["platforms"]]
            genres = []
            if "genres" in g:
                genres = [ge["name"] for ge in g["genres"]]
            games.append({
                "igdb_id": g["id"],
                "name": g["name"],
                "cover_url": f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_id}.jpg" if cover_id else None,
                "release_year": release_year,
                "platforms": ", ".join(platforms),
                "genres": ", ".join(genres),
                "summary": g.get("summary", ""),
            })
        return games


    def get_game_by_id(self, igdb_id):
        """Fetch a single game by IGDB ID, parsed."""
        body = (
            f"fields id, name, cover.image_id, first_release_date,"
            f" platforms.abbreviation, genres.name, summary;"
            f" where id = {igdb_id};"
        )
        results = self._request("games", body)
        if not results:
            return None
        g = results[0]
        cover_id = None
        if "cover" in g and "image_id" in g["cover"]:
            cover_id = g["cover"]["image_id"]
        release_year = None
        if "first_release_date" in g:
            release_year = time.gmtime(g["first_release_date"]).tm_year
        platforms = []
        if "platforms" in g:
            platforms = [p.get("abbreviation", "?") for p in g["platforms"]]
        genres = []
        if "genres" in g:
            genres = [ge["name"] for ge in g["genres"]]
        return {
            "igdb_id": g["id"],
            "name": g["name"],
            "cover_url": f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_id}.jpg" if cover_id else None,
            "release_year": release_year,
            "platforms": ", ".join(platforms),
            "genres": ", ".join(genres),
            "summary": g.get("summary", ""),
        }
