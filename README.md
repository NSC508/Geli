# 🎮📚🎬📺 Geli — Multi-Media Ranking App

**Geli** is a personal ranking app inspired by the [Beli](https://beliapp.com/) restaurant-rating experience. Search for any **video game**, **book**, **movie**, or **TV show**, rate it as **Like**, **Neutral**, or **Dislike**, then stack-rank it against your other picks through quick pairwise comparisons. Once you've ranked at least 10 items in a category, Geli automatically calculates a **1–10 score** for every title on your list.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎮📚🎬📺 **Multi-Media** | Rank video games, books, movies, and TV shows — each with their own standalone experience |
| 🔍 **Search** | Search across IGDB (games), Open Library (books), and TMDB (movies & TV) |
| 👍👎 **Tier Rating** | Classify every item as **Like**, **Neutral**, or **Dislike** |
| ⚖️ **Pairwise Comparison** | Binary-search-based comparison flow to precisely rank within tiers |
| 📊 **Automatic Scoring** | Once you hit 10+ items, scores from 1.0 – 10.0 are calculated per tier |
| 🗑️ **Remove Items** | Remove any item from your rankings |
| 🌙 **Dark Glassmorphism UI** | A sleek, modern dark-themed interface with per-media accent colors |
| 🔄 **Media Switcher** | Click the Geli logo to switch between media types |

---

## 📋 Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.11+ | Tested on 3.11 via Conda |
| **pip** or **Conda** | any | For installing Python packages |
| **Twitch/IGDB API Credentials** | — | Free (for games — see [below](#-igdb-api-credentials)) |
| **TMDB API Key** | — | Free (for movies & TV — see [below](#-tmdb-api-key)) |

> 💡 **Books** use the Open Library API which requires **no API key**.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/NSC508/Geli.git
cd Geli
```

### 2. Set Up the Python Environment

You can use **Conda** (recommended) or a plain **virtualenv**.

<details>
<summary><strong>Option A — Conda (recommended)</strong></summary>

```bash
# Create and activate a new environment
conda create -n geli python=3.11 -y
conda activate geli

# Install dependencies
pip install flask requests
```

</details>

<details>
<summary><strong>Option B — virtualenv / venv</strong></summary>

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install flask requests
```

</details>

### 3. Obtain API Credentials

#### 🎮 IGDB API Credentials (for Games)

1. Go to the [Twitch Developer Console](https://dev.twitch.tv/console).
2. Log in (or create a free Twitch account).
3. Click **Register Your Application**.
4. Fill in:
   - **Name**: anything (e.g. `Geli`)
   - **OAuth Redirect URLs**: `http://localhost`
   - **Category**: `Application Integration`
5. Click **Create**, then click **Manage** on the new app.
6. Copy your **Client ID**.
7. Click **New Secret** and copy the **Client Secret**.

#### 🎬📺 TMDB API Key (for Movies & TV Shows)

1. Go to [TMDB](https://www.themoviedb.org/) and create a free account.
2. Go to **Settings** → **API** → **Request an API Key**.
3. Select **Developer**, accept the terms, and fill in the application details.
4. Copy your **API Key (v3 auth)**.

### 4. Configure Credentials

Choose **one** of the two methods below. **Environment variables** are recommended because they keep secrets out of files entirely.

<details>
<summary><strong>Option A — Environment variables (recommended)</strong></summary>

```bash
export IGDB_CLIENT_ID="your_client_id_here"
export IGDB_CLIENT_SECRET="your_client_secret_here"
export TMDB_API_KEY="your_tmdb_api_key_here"
```

> 💡 **Tip:** Add these lines to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) so they persist across sessions.

</details>

<details>
<summary><strong>Option B — <code>creds.json</code> file</strong></summary>

```bash
cp creds.example.json creds.json
```

Then edit `creds.json` and replace the placeholder values:

```json
{
    "client_id": "your_twitch_client_id_here",
    "client_secret": "your_twitch_client_secret_here",
    "tmdb_api_key": "your_tmdb_api_key_here"
}
```

> ⚠️ **Important:** `creds.json` is listed in `.gitignore` and will **never** be committed to Git.

</details>

### 5. Run the App

```bash
python app.py
```

The app will start on **http://localhost:5000**. Open this URL in your browser.

---

## 🎯 How to Use

1. **Switch Media** — Click the **Geli logo** in the navbar to switch between Games, Books, Movies, and TV Shows.
2. **Add Items** — Click **+ Add Game/Book/Movie/Show** in the navbar and search.
3. **Rate It** — Click a search result and choose **Like**, **Neutral**, or **Dislike**.
4. **Compare** — If there are other items in the same tier, you'll be asked "Which is better?" comparisons.
5. **View Rankings** — The home page shows your full ranked list, split by tier.
6. **Scores Unlock at 10 Items** — Once you've ranked 10+ items in a media type, numerical scores appear.
7. **Remove** — Click the ✕ button on any card to remove it from your rankings.

---

## 🗂️ Project Structure

```
Geli/
├── app.py                  # Flask application — multi-media routes & API endpoints
├── igdb_client.py          # IGDB / Twitch API client (games)
├── openlibrary_client.py   # Open Library API client (books)
├── tmdb_client.py          # TMDB API client (movies & TV shows)
├── models.py               # SQLite data layer with media_type support
├── ranking.py              # Binary insertion ranking algorithm & score calculation
├── static/
│   ├── style.css           # Dark glassmorphism theme with per-media accents
│   └── app.js              # Client-side search, rating, comparison, media switcher
├── templates/
│   ├── base.html           # Base layout with navbar & media switcher dropdown
│   ├── index.html          # Rankings page (adaptive to media type)
│   ├── search.html         # Search & rating page (adaptive to media type)
│   └── compare.html        # Pairwise comparison page (adaptive to media type)
├── creds.example.json      # Template for API credentials
├── .gitignore              # Keeps secrets & DB out of version control
└── README.md               # You are here!
```

---

## 🔧 Configuration Reference

| Variable / File | Purpose | Required |
|---|---|---|
| `IGDB_CLIENT_ID` | Twitch / IGDB client ID | Yes for games (env var **or** `creds.json`) |
| `IGDB_CLIENT_SECRET` | Twitch / IGDB client secret | Yes for games (env var **or** `creds.json`) |
| `TMDB_API_KEY` | TMDB v3 API key | Yes for movies & TV (env var **or** `creds.json`) |
| `creds.json` | File-based credential store | No (fallback if env vars are unset) |

> 💡 **Books** use Open Library which requires **no credentials** at all.

---

## 🤝 Contributing

Pull requests are welcome! If you have ideas for new features or find a bug:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- Game data provided by [IGDB](https://www.igdb.com/) via the Twitch API
- Book data provided by [Open Library](https://openlibrary.org/)
- Movie & TV data provided by [TMDB](https://www.themoviedb.org/)
- Inspired by [Beli](https://beliapp.com/)