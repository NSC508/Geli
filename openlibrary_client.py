"""Open Library API client — no authentication required."""
import requests


class OpenLibraryClient:
    SEARCH_URL = "https://openlibrary.org/search.json"
    COVER_BASE = "https://covers.openlibrary.org/b/id"

    def search_books(self, query, limit=20):
        """Search Open Library for books by title/author. Returns list of book dicts."""
        resp = requests.get(self.SEARCH_URL, params={
            "q": query,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,cover_i,subject,edition_count",
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        books = []
        for doc in data.get("docs", []):
            cover_i = doc.get("cover_i")
            authors = doc.get("author_name", [])
            subjects = doc.get("subject", [])[:3]  # Limit to first 3 subjects

            books.append({
                "external_id": doc.get("key", "").replace("/works/", ""),
                "name": doc.get("title", "Unknown"),
                "cover_url": f"{self.COVER_BASE}/{cover_i}-M.jpg" if cover_i else None,
                "release_year": doc.get("first_publish_year"),
                "meta_line": ", ".join(authors[:3]) if authors else "",
                "genres": ", ".join(subjects) if subjects else "",
                "summary": f"{doc.get('edition_count', 0)} editions" if doc.get("edition_count") else "",
            })
        return books

    def get_book_by_id(self, work_id):
        """Fetch a single book by Open Library work key."""
        url = f"https://openlibrary.org/works/{work_id}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        # Get author names
        authors = []
        for author_ref in data.get("authors", []):
            author_obj = author_ref.get("author", author_ref)
            author_key = author_obj.get("key", "")
            if author_key:
                try:
                    a_resp = requests.get(f"https://openlibrary.org{author_key}.json", timeout=5)
                    if a_resp.ok:
                        authors.append(a_resp.json().get("name", "Unknown"))
                except Exception:
                    pass

        covers = data.get("covers", [])
        cover_id = covers[0] if covers else None
        subjects = data.get("subjects", [])[:3]

        description = data.get("description", "")
        if isinstance(description, dict):
            description = description.get("value", "")

        return {
            "external_id": work_id,
            "name": data.get("title", "Unknown"),
            "cover_url": f"{self.COVER_BASE}/{cover_id}-M.jpg" if cover_id else None,
            "release_year": None,
            "meta_line": ", ".join(authors),
            "genres": ", ".join(subjects),
            "summary": description[:300] if description else "",
        }
