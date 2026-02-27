/* ═══════════════════════════════════════════════════
   Geli — Client-side JavaScript
   ═══════════════════════════════════════════════════ */

let searchTimeout = null;
let selectedGame = null;

// ── Search Page Logic ────────────────────────────────

const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        const spinner = document.getElementById('searchSpinner');
        const resultsDiv = document.getElementById('searchResults');

        if (query.length < 2) {
            resultsDiv.innerHTML = '';
            spinner.classList.remove('active');
            return;
        }

        spinner.classList.add('active');

        searchTimeout = setTimeout(async () => {
            try {
                const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const games = await resp.json();
                spinner.classList.remove('active');

                if (games.error) {
                    resultsDiv.innerHTML = `<div class="no-results">Error: ${games.error}</div>`;
                    return;
                }

                if (games.length === 0) {
                    resultsDiv.innerHTML = '<div class="no-results">No games found. Try a different search.</div>';
                    return;
                }

                resultsDiv.innerHTML = games.map(game => `
                    <div class="search-result-card ${game.already_ranked ? 'already-ranked' : ''}"
                         onclick="${game.already_ranked ? '' : `openRatingModal(${escapeAttr(JSON.stringify(game))})`}">
                        <div class="search-result-cover">
                            ${game.cover_url
                        ? `<img src="${game.cover_url}" alt="${escapeHtml(game.name)}" loading="lazy">`
                        : '<div class="no-cover">🎮</div>'}
                        </div>
                        <div class="search-result-info">
                            <div class="search-result-title">${escapeHtml(game.name)}</div>
                            <div class="search-result-meta">
                                ${game.release_year ? game.release_year : ''}
                                ${game.platforms ? ' · ' + escapeHtml(game.platforms) : ''}
                                ${game.genres ? ' · ' + escapeHtml(game.genres) : ''}
                            </div>
                        </div>
                        ${game.already_ranked
                        ? '<span class="search-result-badge">Already Ranked</span>'
                        : '<span class="search-result-badge">+ Rate</span>'}
                    </div>
                `).join('');
            } catch (err) {
                spinner.classList.remove('active');
                resultsDiv.innerHTML = `<div class="no-results">Search failed. Please try again.</div>`;
            }
        }, 350);  // Debounce 350ms
    });
}

// ── Rating Modal ─────────────────────────────────────

function openRatingModal(game) {
    selectedGame = game;
    const modal = document.getElementById('ratingModal');
    const cover = document.getElementById('modalCover');
    const title = document.getElementById('modalTitle');
    const meta = document.getElementById('modalMeta');
    const summary = document.getElementById('modalSummary');

    cover.src = game.cover_url || '';
    cover.style.display = game.cover_url ? 'block' : 'none';
    title.textContent = game.name;

    let metaText = '';
    if (game.release_year) metaText += game.release_year;
    if (game.platforms) metaText += ' · ' + game.platforms;
    if (game.genres) metaText += ' · ' + game.genres;
    meta.textContent = metaText;

    summary.textContent = game.summary || '';

    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('ratingModal').style.display = 'none';
    selectedGame = null;
}

async function rateGame(tier) {
    if (!selectedGame) return;

    // Disable buttons during request
    document.querySelectorAll('.rate-btn').forEach(btn => btn.disabled = true);

    try {
        const resp = await fetch('/api/rate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game: selectedGame, tier: tier }),
        });
        const data = await resp.json();

        if (data.error) {
            showToast('⚠️ ' + data.error);
            document.querySelectorAll('.rate-btn').forEach(btn => btn.disabled = false);
            return;
        }

        closeModal();
        window.location.href = data.redirect;
    } catch (err) {
        showToast('Failed to rate game. Please try again.');
        document.querySelectorAll('.rate-btn').forEach(btn => btn.disabled = false);
    }
}

// ── Comparison Page Logic ────────────────────────────

async function submitComparison(answer) {
    // Add visual feedback on the clicked card
    const clickedCard = answer === 'better'
        ? document.getElementById('cardNew')
        : document.getElementById('cardExisting');
    if (clickedCard) clickedCard.classList.add('selected');

    // Disable both cards
    document.querySelectorAll('.compare-card.clickable').forEach(c => {
        c.style.pointerEvents = 'none';
    });

    try {
        const resp = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: answer }),
        });
        const data = await resp.json();

        if (data.error) {
            showToast('⚠️ ' + data.error);
            document.querySelectorAll('.compare-card.clickable').forEach(c => {
                c.style.pointerEvents = '';
                c.classList.remove('selected');
            });
            return;
        }

        window.location.href = data.redirect;
    } catch (err) {
        showToast('Comparison failed. Please try again.');
        document.querySelectorAll('.compare-card.clickable').forEach(c => {
            c.style.pointerEvents = '';
            c.classList.remove('selected');
        });
    }
}

// ── Remove Game ──────────────────────────────────────

async function removeGame(igdbId, name) {
    if (!confirm(`Remove "${name}" from your rankings?`)) return;

    try {
        const resp = await fetch('/api/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ igdb_id: igdbId }),
        });
        const data = await resp.json();

        if (data.status === 'ok') {
            showToast(`Removed "${name}"`);
            setTimeout(() => location.reload(), 500);
        }
    } catch (err) {
        showToast('Failed to remove game.');
    }
}

// ── Utilities ────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});
