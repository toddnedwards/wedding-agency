// Mobile Menu Toggle
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

if (hamburger) {
    hamburger.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });
}

// Close mobile menu when a link is clicked
const navLinks = document.querySelectorAll('.nav-menu a');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
    });
});

// Mega menu toggle for touch/mobile interactions
const megaWrappers = document.querySelectorAll('.mega-menu-wrapper');
megaWrappers.forEach(wrapper => {
    const toggle = wrapper.querySelector('.mega-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        const isOpen = wrapper.classList.contains('open');

        megaWrappers.forEach(item => {
            item.classList.remove('open');
            const itemToggle = item.querySelector('.mega-toggle');
            if (itemToggle) {
                itemToggle.setAttribute('aria-expanded', 'false');
            }
        });

        if (!isOpen) {
            wrapper.classList.add('open');
            toggle.setAttribute('aria-expanded', 'true');
        }
    });
});

document.addEventListener('click', (e) => {
    megaWrappers.forEach(wrapper => {
        if (!wrapper.contains(e.target)) {
            wrapper.classList.remove('open');
            const toggle = wrapper.querySelector('.mega-toggle');
            if (toggle) {
                toggle.setAttribute('aria-expanded', 'false');
            }
        }
    });
});

// Form validation
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', (e) => {
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.style.borderColor = 'var(--danger)';
            } else {
                input.style.borderColor = 'var(--border-color)';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
        }
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const stickyHeader = document.querySelector('nav');
            const headerOffset = stickyHeader ? stickyHeader.getBoundingClientRect().height + 16 : 16;
            const targetTop = target.getBoundingClientRect().top + window.scrollY - headerOffset;
            window.scrollTo({ top: targetTop, behavior: 'smooth' });
        }
    });
});

// Add animation to elements on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.card, section').forEach(element => {
    observer.observe(element);
});

function trackFunnelEvent(eventName, payload = {}) {
    if (!eventName) return;
    const detail = {
        event: eventName,
        path: window.location.pathname,
        timestamp: new Date().toISOString(),
        ...payload,
    };

    if (Array.isArray(window.dataLayer)) {
        window.dataLayer.push(detail);
    }

    document.dispatchEvent(new CustomEvent('funnel:event', { detail }));

    const endpoint = document.body ? document.body.getAttribute('data-funnel-event-url') : '';
    if (!endpoint) return;

    const body = JSON.stringify(detail);
    try {
        if (navigator.sendBeacon) {
            const blob = new Blob([body], { type: 'application/json' });
            navigator.sendBeacon(endpoint, blob);
            return;
        }
    } catch (error) {
        // Fall through to fetch when sendBeacon is unavailable or fails.
    }

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body,
        credentials: 'same-origin',
    }).catch(() => {
        // Tracking should never block UX.
    });
}

// Close alerts automatically
const alerts = document.querySelectorAll('.alert');
alerts.forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
});

// Clickable cards: make whole card open details while preserving nested controls.
const clickableCards = document.querySelectorAll('.js-vendor-card-link');
const interactiveSelector = 'a, button, input, select, textarea, label, [role="button"], [role="link"]';

clickableCards.forEach((card) => {
    const href = card.getAttribute('data-card-link');
    if (!href) return;

    card.addEventListener('click', (event) => {
        const target = event.target;
        if (target instanceof Element && target.closest(interactiveSelector)) {
            return;
        }
        trackFunnelEvent('vendor_card_click', {
            destination: href,
            vendorName: card.getAttribute('aria-label') || '',
        });
        window.location.href = href;
    });

    card.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }

        const target = event.target;
        if (target instanceof Element && target !== card && target.closest(interactiveSelector)) {
            return;
        }

        event.preventDefault();
        trackFunnelEvent('vendor_card_click', {
            destination: href,
            vendorName: card.getAttribute('aria-label') || '',
        });
        window.location.href = href;
    });
});

// Liked acts (client-side)
const likedActsStorageKey = 'likedActs';

function normalizeActId(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';

    const colonMatch = raw.match(/^(musicians|caricaturists|photographers):(\d+)$/);
    if (colonMatch) {
        return `${colonMatch[1]}:${colonMatch[2]}`;
    }

    const dashMatch = raw.match(/^(musicians|caricaturists|photographers)-(\d+)$/);
    if (dashMatch) {
        return `${dashMatch[1]}:${dashMatch[2]}`;
    }

    return '';
}

function readLikedActs() {
    try {
        const raw = window.localStorage.getItem(likedActsStorageKey);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return [];

        const cleaned = [];
        const seen = new Set();

        parsed.forEach((item) => {
            if (!item || !item.name || !item.url) return;
            const normalizedId = normalizeActId(item.id);
            if (!normalizedId || seen.has(normalizedId)) return;
            seen.add(normalizedId);

            cleaned.push({
                ...item,
                id: normalizedId,
            });
        });

        return cleaned;
    } catch (error) {
        return [];
    }
}

function writeLikedActs(items) {
    window.localStorage.setItem(likedActsStorageKey, JSON.stringify(items));
}

function findLikedIndex(items, id) {
    return items.findIndex((item) => item.id === id);
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function buttonToAct(button) {
    if (!button || !button.dataset) return null;
    const act = {
        id: normalizeActId(button.dataset.actId || ''),
        name: (button.dataset.actName || '').trim(),
        url: (button.dataset.actUrl || '').trim(),
        type: (button.dataset.actType || '').trim(),
        location: (button.dataset.actLocation || '').trim(),
        image: (button.dataset.actImage || '').trim()
    };

    if (!act.id || !act.name || !act.url) return null;
    return act;
}

function setLikeButtonVisualState(button, isLiked) {
    const heart = button.querySelector('[data-heart-icon]');
    button.classList.toggle('is-liked', isLiked);
    button.setAttribute('aria-pressed', isLiked ? 'true' : 'false');
    button.setAttribute('title', isLiked ? 'Remove from liked acts' : 'Like this act');
    if (heart) {
        heart.textContent = isLiked ? '♥' : '♡';
    }
}

function updateLikedCount(count) {
    const countEls = document.querySelectorAll('[data-liked-count]');
    countEls.forEach((el) => {
        el.textContent = String(count);
    });
}

function updateAllLikeButtons() {
    const likedActs = readLikedActs();
    const likedIds = new Set(likedActs.map((item) => item.id));
    const buttons = document.querySelectorAll('.js-like-act-toggle');

    buttons.forEach((button) => {
        const act = buttonToAct(button);
        if (!act) return;
        setLikeButtonVisualState(button, likedIds.has(act.id));
    });
}

function renderLikedActsPanel() {
    const panel = document.getElementById('liked-acts-panel');
    if (!panel) return;

    const listEl = panel.querySelector('[data-liked-list]');
    const emptyEl = panel.querySelector('[data-liked-empty]');
    const searchEl = panel.querySelector('[data-liked-search]');
    if (!listEl || !emptyEl) return;

    const searchTerm = (searchEl ? searchEl.value : '').trim().toLowerCase();
    const likedActs = readLikedActs();
    const existingCta = panel.querySelector('[data-liked-multi-enquiry]');
    if (existingCta) {
        existingCta.remove();
    }

    const filtered = likedActs.filter((item) => {
        if (!searchTerm) return true;
        const haystack = `${item.name} ${item.type || ''} ${item.location || ''}`.toLowerCase();
        return haystack.includes(searchTerm);
    });

    if (!filtered.length) {
        listEl.innerHTML = '';
        emptyEl.hidden = false;
        emptyEl.textContent = likedActs.length
            ? 'No liked acts match your search.'
            : 'No liked acts yet.';
        return;
    }

    emptyEl.hidden = true;
    listEl.innerHTML = filtered.map((item) => {
        const metaParts = [item.type, item.location].filter(Boolean);
        const meta = metaParts.join(' • ');
        return `
            <article class="liked-act-item">
                <div>
                    <p class="liked-act-name"><a href="${escapeHtml(item.url)}">${escapeHtml(item.name)}</a></p>
                    <p class="liked-act-meta">${escapeHtml(meta || 'Saved act')}</p>
                </div>
                <button type="button" class="liked-act-remove" data-remove-liked-id="${escapeHtml(item.id)}">Remove</button>
            </article>
        `;
    }).join('');

    const validSelectedActs = likedActs
        .filter((item) => normalizeActId(item.id))
        .map((item) => ({ ...item, id: normalizeActId(item.id) }));

    if (validSelectedActs.length > 1) {
        const actsToken = validSelectedActs
            .map((item) => `${item.id || ''}`.trim())
            .filter(Boolean)
            .join('|');
        const baseMultiUrl = panel.getAttribute('data-multi-enquiry-url') || '/bookings/enquiry/multi/';
        const separator = baseMultiUrl.includes('?') ? '&' : '?';
        const params = new URLSearchParams();
        params.set('acts', actsToken);

        const pageParams = new URLSearchParams(window.location.search || '');
        const carryKeys = ['event_date', 'available_date', 'event_type', 'event_location', 'county', 'budget'];
        carryKeys.forEach((key) => {
            const value = pageParams.get(key);
            if (value) {
                if (key === 'available_date' && !params.get('event_date')) {
                    params.set('event_date', value);
                } else {
                    params.set(key, value);
                }
            }
        });

        const multiUrl = `${baseMultiUrl}${separator}${params.toString()}`;

        const cta = document.createElement('div');
        cta.className = 'liked-multi-enquiry';
        cta.setAttribute('data-liked-multi-enquiry', 'true');
        cta.innerHTML = `
            <p>Too many great people to choose from? Enquire for all of them now and we'll get back to you with all the best options!</p>
            <a class="btn btn-primary" href="${multiUrl}" data-track-event="multi_enquiry_click" data-track-context="liked_panel">Enquire for all</a>
        `;
        panel.appendChild(cta);
    }
}

function refreshLikedUi() {
    const likedActs = readLikedActs();
    updateLikedCount(likedActs.length);
    updateAllLikeButtons();
    renderLikedActsPanel();
}

function toggleActFromButton(button) {
    const act = buttonToAct(button);
    if (!act) return;

    const likedActs = readLikedActs();
    const existingIndex = findLikedIndex(likedActs, act.id);

    if (existingIndex >= 0) {
        likedActs.splice(existingIndex, 1);
    } else {
        likedActs.push(act);
    }

    writeLikedActs(likedActs);
    refreshLikedUi();
}

const likeButtons = document.querySelectorAll('.js-like-act-toggle');
likeButtons.forEach((button) => {
    button.addEventListener('click', () => {
        toggleActFromButton(button);
    });
});

const likedPanel = document.getElementById('liked-acts-panel');
const likedBackdrop = document.querySelector('[data-liked-backdrop]');
const likedToggles = document.querySelectorAll('[data-liked-toggle]');
const likedClose = document.querySelector('[data-liked-close]');
const likedSearch = document.querySelector('[data-liked-search]');

function setLikedPanelOpen(isOpen) {
    if (!likedPanel) return;
    likedPanel.classList.toggle('open', isOpen);
    likedPanel.setAttribute('aria-hidden', isOpen ? 'false' : 'true');

    likedToggles.forEach((toggle) => {
        toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    if (likedBackdrop) {
        likedBackdrop.hidden = !isOpen;
    }

    if (isOpen && likedSearch) {
        likedSearch.focus();
    }
}

likedToggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
        const openNow = likedPanel && likedPanel.classList.contains('open');
        setLikedPanelOpen(!openNow);
    });
});

if (likedClose) {
    likedClose.addEventListener('click', () => setLikedPanelOpen(false));
}

if (likedBackdrop) {
    likedBackdrop.addEventListener('click', () => setLikedPanelOpen(false));
}

if (likedSearch) {
    likedSearch.addEventListener('input', () => {
        renderLikedActsPanel();
    });
}

if (likedPanel) {
    likedPanel.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        const removeButton = target.closest('[data-remove-liked-id]');
        if (!removeButton) return;

        const id = removeButton.getAttribute('data-remove-liked-id');
        if (!id) return;

        const likedActs = readLikedActs().filter((item) => item.id !== id);
        writeLikedActs(likedActs);
        refreshLikedUi();
    });
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && likedPanel && likedPanel.classList.contains('open')) {
        setLikedPanelOpen(false);
    }
});

document.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const tracked = target.closest('[data-track-event]');
    if (!tracked) return;

    const eventName = tracked.getAttribute('data-track-event');
    if (!eventName) return;

    trackFunnelEvent(eventName, {
        context: tracked.getAttribute('data-track-context') || '',
        vendor: tracked.getAttribute('data-track-vendor') || '',
        vendorType: tracked.getAttribute('data-track-vendor-type') || '',
        href: tracked.getAttribute('href') || '',
    });
});

document.querySelectorAll('form[data-track-submit]').forEach((form) => {
    form.addEventListener('submit', () => {
        const eventName = form.getAttribute('data-track-submit');
        if (!eventName) return;

        trackFunnelEvent(eventName, {
            context: form.getAttribute('data-track-context') || '',
            vendor: form.getAttribute('data-track-vendor') || '',
            vendorType: form.getAttribute('data-track-vendor-type') || '',
        });
    });
});

refreshLikedUi();