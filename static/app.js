/* ═══════════════════════════════════════════════════
   Geli — Client-side JavaScript (Multi-Media)
   ═══════════════════════════════════════════════════ */

const mediaType = document.body.dataset.mediaType || 'games';
let searchTimeout = null;
let selectedItem = null;

const MEDIA_EMOJI = {
    games: '🎮',
    books: '📚',
    movies: '🎬',
    tv: '📺',
};

// ── Media Switcher Dropdown ──────────────────────────

const mediaToggle = document.getElementById('mediaToggle');
const mediaDropdown = document.getElementById('mediaDropdown');

if (mediaToggle && mediaDropdown) {
    mediaToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        mediaDropdown.classList.toggle('open');
    });

    document.addEventListener('click', () => {
        mediaDropdown.classList.remove('open');
    });

    mediaDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

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
                const resp = await fetch(`/${mediaType}/api/search?q=${encodeURIComponent(query)}`);
                const items = await resp.json();
                spinner.classList.remove('active');

                if (items.error) {
                    resultsDiv.innerHTML = `<div class="no-results">Error: ${items.error}</div>`;
                    return;
                }

                if (items.length === 0) {
                    resultsDiv.innerHTML = '<div class="no-results">No results found. Try a different search.</div>';
                    return;
                }

                const emoji = MEDIA_EMOJI[mediaType] || '🎮';

                resultsDiv.innerHTML = items.map(item => `
                    <div class="search-result-card ${item.already_ranked ? 'already-ranked' : ''}"
                         onclick="${item.already_ranked ? '' : `openRatingModal(${escapeAttr(JSON.stringify(item))})`}">
                        <div class="search-result-cover">
                            ${item.cover_url
                        ? `<img src="${item.cover_url}" alt="${escapeHtml(item.name)}" loading="lazy">`
                        : `<div class="no-cover">${emoji}</div>`}
                        </div>
                        <div class="search-result-info">
                            <div class="search-result-title">${escapeHtml(item.name)}</div>
                            <div class="search-result-meta">
                                ${item.release_year ? item.release_year : ''}
                                ${item.meta_line ? ' · ' + escapeHtml(item.meta_line) : ''}
                                ${item.genres ? ' · ' + escapeHtml(item.genres) : ''}
                            </div>
                        </div>
                        ${item.already_ranked
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

function openRatingModal(item) {
    selectedItem = item;
    const modal = document.getElementById('ratingModal');
    const cover = document.getElementById('modalCover');
    const title = document.getElementById('modalTitle');
    const meta = document.getElementById('modalMeta');
    const summary = document.getElementById('modalSummary');

    cover.src = item.cover_url || '';
    cover.style.display = item.cover_url ? 'block' : 'none';
    title.textContent = item.name;

    let metaText = '';
    if (item.release_year) metaText += item.release_year;
    if (item.meta_line) metaText += ' · ' + item.meta_line;
    if (item.genres) metaText += ' · ' + item.genres;
    meta.textContent = metaText;

    summary.textContent = item.summary || '';

    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('ratingModal').style.display = 'none';
    selectedItem = null;
}

async function rateItem(tier) {
    if (!selectedItem) return;

    // Disable buttons during request
    document.querySelectorAll('.rate-btn').forEach(btn => btn.disabled = true);

    try {
        const resp = await fetch(`/${mediaType}/api/rate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item: selectedItem, tier: tier }),
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
        showToast('Failed to rate. Please try again.');
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
        const resp = await fetch(`/${mediaType}/api/compare`, {
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

// ── Remove Item ──────────────────────────────────────

async function removeItem(externalId, name) {
    if (!confirm(`Remove "${name}" from your rankings?`)) return;

    try {
        const resp = await fetch(`/${mediaType}/api/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ external_id: externalId }),
        });
        const data = await resp.json();

        if (data.status === 'ok') {
            showToast(`Removed "${name}"`);
            setTimeout(() => location.reload(), 500);
        }
    } catch (err) {
        showToast('Failed to remove.');
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
