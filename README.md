# 🎮 Geli — Video Game Ranking App

**Geli** is a personal video game ranking app inspired by the [Beli](https://beliapp.com/) restaurant-rating experience. Search for any game, rate it as **Like**, **Neutral**, or **Dislike**, then stack-rank it against your other games through quick pairwise comparisons. Once you've ranked at least 10 games, Geli automatically calculates a **1–10 score** for every title on your list.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Game Search** | Search the IGDB database for any video game — with cover art, genres, platforms, and release year |
| 👍👎 **Tier Rating** | Classify every game as **Like**, **Neutral**, or **Dislike** |
| ⚖️ **Pairwise Comparison** | Binary-search-based comparison flow to precisely rank a new game within its tier |
| 📊 **Automatic Scoring** | Once you hit 10+ games, scores from 1.0 – 10.0 are calculated per tier (Liked: 7–10, Neutral: 4–7, Disliked: 1–4) |
| 🗑️ **Remove Games** | Changed your mind? Remove any game from your rankings |
| 🌙 **Dark Glassmorphism UI** | A sleek, modern dark-themed interface with glass effects and smooth animations |

---

## 📋 Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.11+ | Tested on 3.11 via Conda |
| **pip** or **Conda** | any | For installing Python packages |
| **Twitch/IGDB API Credentials** | — | Free to obtain (see [below](#-igdb-api-credentials)) |

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

### 3. Obtain IGDB API Credentials

Geli uses the **IGDB API** (powered by Twitch) to search for game data. You'll need a free Twitch developer account:

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

### 4. Configure Credentials

Choose **one** of the two methods below. **Environment variables** are recommended because they keep secrets out of files entirely.

<details>
<summary><strong>Option A — Environment variables (recommended)</strong></summary>

```bash
export IGDB_CLIENT_ID="your_client_id_here"
export IGDB_CLIENT_SECRET="your_client_secret_here"
```

> 💡 **Tip:** Add these lines to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) so they persist across sessions.

</details>

<details>
<summary><strong>Option B — <code>creds.json</code> file</strong></summary>

```bash
cp creds.example.json creds.json
```

Then edit `creds.json` and replace the placeholder values with your real credentials:

```json
{
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here"
}
```

> ⚠️ **Important:** `creds.json` is listed in `.gitignore` and will **never** be committed to Git. Do not rename or remove it from `.gitignore`.

</details>

### 5. Run the App

```bash
python app.py
```

The app will start on **http://localhost:5000**. Open this URL in your browser.

---

## 🎯 How to Use

1. **Add Games** — Click **+ Add Game** in the navbar and search for a game.
2. **Rate It** — Click a search result and choose **Like**, **Neutral**, or **Dislike**.
3. **Compare** — If there are other games in the same tier, you'll be asked a series of "Which do you prefer?" comparisons to place the new game precisely.
4. **View Rankings** — The home page shows your full ranked list, split by tier.
5. **Scores Unlock at 10 Games** — Once you've ranked 10+ games, numerical scores (1.0–10.0) appear automatically.
6. **Remove** — Click the ✕ button on any game card to remove it from your rankings.

---

## 🗂️ Project Structure

```
Geli/
├── app.py               # Flask application — routes & API endpoints
├── igdb_client.py       # IGDB / Twitch API client with auto-token refresh
├── models.py            # SQLite data layer (game storage & ranking)
├── ranking.py           # Binary insertion ranking algorithm & score calculation
├── static/
│   ├── style.css        # Dark glassmorphism theme
│   └── app.js           # Client-side search, rating modal, comparison logic
├── templates/
│   ├── base.html        # Base layout with navbar
│   ├── index.html       # Rankings page
│   ├── search.html      # Game search & rating page
│   └── compare.html     # Pairwise comparison page
├── creds.example.json   # Template for API credentials
├── .gitignore           # Keeps secrets & DB out of version control
└── README.md            # You are here!
```

---

## 🔧 Configuration Reference

| Variable / File | Purpose | Required |
|---|---|---|
| `IGDB_CLIENT_ID` | Twitch / IGDB client ID | Yes (env var **or** `creds.json`) |
| `IGDB_CLIENT_SECRET` | Twitch / IGDB client secret | Yes (env var **or** `creds.json`) |
| `creds.json` | Alternative file-based credential store | No (fallback if env vars are unset) |

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
- Inspired by [Beli](https://beliapp.com/)