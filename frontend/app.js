// Configuration
const API_BASE_URL = 'http://localhost:8000';
const CHATGPT_AVG_SIZE = 45000;

// State
let state = {
    theme: localStorage.getItem('theme') || 'light',
    currentCategory: 'all',
    totalQueries: parseInt(localStorage.getItem('totalQueries')) || 0,
    offlineQueries: parseInt(localStorage.getItem('offlineQueries')) || 0,
    totalBytesSaved: parseInt(localStorage.getItem('totalBytesSaved')) || 0,
    recentQueries: JSON.parse(localStorage.getItem('recentQueries')) || [],
    isOnline: navigator.onLine,
    networkSpeed: 'online' // online, slow, offline
};

// DOM Elements
const elements = {
    darkModeToggle: document.getElementById('dark-mode-toggle'),
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    welcomeCard: document.getElementById('welcome-card'),
    categoryChips: document.querySelectorAll('.chip'),
    suggestedSection: document.getElementById('suggested-section'),
    promptCards: document.querySelectorAll('.prompt-card'),
    responseContainer: document.getElementById('response-container'),
    recentSection: document.getElementById('recent-section'),
    recentQueriesList: document.getElementById('recent-queries-list'),
    queryInput: document.getElementById('query-input'),
    sendBtn: document.getElementById('send-btn'),
    voiceBtn: document.getElementById('voice-btn'),
    voiceIndicator: document.getElementById('voice-indicator'),
    charCounter: document.getElementById('char-counter'),
    bandwidthPanel: document.getElementById('bandwidth-panel'),
    bandwidthClose: document.getElementById('bandwidth-close'),
    loadingOverlay: document.getElementById('loading-overlay'),
    toastContainer: document.getElementById('toast-container')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initServiceWorker();
    initVoiceRecognition();
    initEventListeners();
    updateNetworkStatus();
    renderRecentQueries();
});

// Theme Management
function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
}

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('theme', state.theme);
    updateThemeIcon();
    showToast('थीम बदल गई', 'success');
}

function updateThemeIcon() {
    if (elements.darkModeToggle) {
        elements.darkModeToggle.textContent = state.theme === 'light' ? '🌙' : '☀️';
    }
}

// Service Worker
async function initServiceWorker() {
    if ('serviceWorker' in navigator) {
        try {
            await navigator.serviceWorker.register('sw.js');
            console.log('Service Worker registered');
        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }
}

// Voice Recognition
let recognition = null;

function initVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'hi-IN';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            elements.voiceIndicator.classList.remove('hidden');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            elements.queryInput.value = transcript;
            handleQuery();
        };

        recognition.onend = () => {
            elements.voiceIndicator.classList.add('hidden');
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            showToast('वॉइस इनपुट में त्रुटि', 'error');
            elements.voiceIndicator.classList.add('hidden');
        };
    } else {
        elements.voiceBtn.disabled = true;
        elements.voiceBtn.style.opacity = '0.5';
    }
}

// Event Listeners
function initEventListeners() {
    // Dark mode toggle
    if (elements.darkModeToggle) {
        elements.darkModeToggle.addEventListener('click', toggleTheme);
    }

    // Category chips
    elements.categoryChips.forEach(chip => {
        chip.addEventListener('click', () => handleCategoryChange(chip));
    });

    // Prompt cards
    elements.promptCards.forEach(card => {
        card.addEventListener('click', () => {
            const query = card.dataset.query;
            elements.queryInput.value = query;
            handleQuery();
        });
    });

    // Send button
    elements.sendBtn.addEventListener('click', handleQuery);

    // Enter key
    elements.queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleQuery();
    });

    // Character counter
    elements.queryInput.addEventListener('input', (e) => {
        const length = e.target.value.length;
        elements.charCounter.textContent = `${length}/200`;
    });

    // Voice button
    elements.voiceBtn.addEventListener('click', () => {
        if (recognition) {
            recognition.start();
        }
    });

    // Bandwidth panel close
    if (elements.bandwidthClose) {
        elements.bandwidthClose.addEventListener('click', () => {
            elements.bandwidthPanel.classList.add('hidden');
        });
    }

    // Online/offline status
    window.addEventListener('online', () => {
        state.isOnline = true;
        state.networkSpeed = 'online';
        updateNetworkStatus();
        showToast('इंटरनेट कनेक्ट हो गया', 'success');
    });

    window.addEventListener('offline', () => {
        state.isOnline = false;
        state.networkSpeed = 'offline';
        updateNetworkStatus();
        showToast('ऑफलाइन मोड', 'warning');
    });
}

// Category Management
function handleCategoryChange(chip) {
    elements.categoryChips.forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    state.currentCategory = chip.dataset.category;
    showToast(`${chip.querySelector('.chip-label').textContent} श्रेणी चुनी गई`, 'success');
}

// Query Handling
async function handleQuery() {
    const query = elements.queryInput.value.trim();
    
    if (!query) {
        showToast('कृपया कोई प्रश्न लिखें', 'warning');
        return;
    }

    // Hide welcome card and suggested section
    if (elements.welcomeCard) {
        elements.welcomeCard.style.display = 'none';
    }
    if (elements.suggestedSection) {
        elements.suggestedSection.style.display = 'none';
    }

    // Clear input
    elements.queryInput.value = '';
    elements.charCounter.textContent = '0/200';
    
    // Show loading
    elements.loadingOverlay.classList.remove('hidden');
    
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: query })
        });
        
        const data = await response.json();
        const endTime = performance.now();
        const responseTime = Math.round(endTime - startTime);
        
        // Add response card
        addResponseCard(query, data, responseTime);
        
        // Update stats
        const bytesUsed = data.bytes_used || 2000;
        updateBandwidthStats(bytesUsed);
        state.totalQueries++;
        
        if (!state.isOnline || data.cached) {
            state.offlineQueries++;
        }
        
        // Add to recent queries
        addToRecentQueries(query);
        renderRecentQueries();
        
        // Show bandwidth panel
        showBandwidthPanel(bytesUsed);
        
    } catch (error) {
        console.error('Query error:', error);
        addErrorCard(query);
        showToast('त्रुटि: सर्वर से कनेक्ट नहीं हो सका', 'error');
    } finally {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// Response Card Management
function addResponseCard(query, data, responseTime) {
    const card = document.createElement('div');
    card.className = 'response-card';
    
    const isOffline = !state.isOnline || data.cached;
    const source = data.source || 'keyword_match';
    
    card.innerHTML = `
        <div class="response-header">
            <div class="response-scheme">
                <span>📋</span>
                <span>${data.scheme_name || 'जानकारी'}</span>
            </div>
            ${isOffline ? '<div class="response-badge offline">📴 ऑफलाइन मोड</div>' : ''}
        </div>
        <div class="response-body">${data.answer}</div>
        <div class="response-footer">
            <div class="response-actions">
                <button class="action-btn" onclick="copyAnswer('${escapeHtml(data.answer)}')">
                    📋 कॉपी करें
                </button>
                <button class="action-btn" onclick="speakAnswer('${escapeHtml(data.answer)}')">
                    🔊 सुनें
                </button>
                ${data.official_link ? `<button class="action-btn" onclick="window.open('${data.official_link}', '_blank')">🔗 आधिकारिक लिंक</button>` : ''}
            </div>
            <div class="response-stats">
                <div class="stat-item">
                    <span>⏱️</span>
                    <span>${responseTime}ms</span>
                </div>
                <div class="stat-item">
                    <span>${getSourceIcon(source)}</span>
                    <span>${getSourceText(source)}</span>
                </div>
            </div>
        </div>
    `;
    
    elements.responseContainer.appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function addErrorCard(query) {
    const card = document.createElement('div');
    card.className = 'response-card';
    card.style.borderColor = 'var(--offline-red)';
    
    card.innerHTML = `
        <div class="response-header">
            <div class="response-scheme">
                <span>❌</span>
                <span>त्रुटि</span>
            </div>
        </div>
        <div class="response-body">क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें।</div>
    `;
    
    elements.responseContainer.appendChild(card);
}

function getSourceIcon(source) {
    const icons = {
        'keyword_match': '⚡',
        'groq_llm': '🤖',
        'fallback': '💬',
        'error': '❌'
    };
    return icons[source] || '💬';
}

function getSourceText(source) {
    const texts = {
        'keyword_match': 'तेज़',
        'groq_llm': 'AI',
        'fallback': 'डिफ़ॉल्ट',
        'error': 'त्रुटि'
    };
    return texts[source] || 'अज्ञात';
}

// Copy Answer
window.copyAnswer = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('उत्तर कॉपी किया गया', 'success');
    }).catch(() => {
        showToast('कॉपी करने में त्रुटि', 'error');
    });
};

// Speak Answer (Text-to-Speech)
window.speakAnswer = function(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'hi-IN';
        utterance.rate = 0.9;
        speechSynthesis.speak(utterance);
        showToast('बोल रहा हूँ...', 'success');
    } else {
        showToast('टेक्स्ट-टू-स्पीच उपलब्ध नहीं', 'error');
    }
};

// Bandwidth Stats
function updateBandwidthStats(bytes) {
    const savings = ((CHATGPT_AVG_SIZE - bytes) / CHATGPT_AVG_SIZE * 100).toFixed(1);
    state.totalBytesSaved += (CHATGPT_AVG_SIZE - bytes);
    localStorage.setItem('totalBytesSaved', state.totalBytesSaved);
}

function showBandwidthPanel(bytes) {
    const kb = (bytes / 1024).toFixed(1);
    const savings = ((CHATGPT_AVG_SIZE - bytes) / CHATGPT_AVG_SIZE * 100).toFixed(0);
    
    document.getElementById('bandwidth-used').textContent = `${kb} KB`;
    document.getElementById('bandwidth-saved').textContent = `${savings}% डेटा बचाया गया`;
    
    elements.bandwidthPanel.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        elements.bandwidthPanel.classList.add('hidden');
    }, 5000);
}

// Recent Queries
function addToRecentQueries(query) {
    state.recentQueries.unshift(query);
    state.recentQueries = state.recentQueries.slice(0, 3); // Keep only last 3
    localStorage.setItem('recentQueries', JSON.stringify(state.recentQueries));
}

function renderRecentQueries() {
    if (state.recentQueries.length === 0) {
        elements.recentSection.classList.add('hidden');
        return;
    }
    
    elements.recentSection.classList.remove('hidden');
    elements.recentQueriesList.innerHTML = state.recentQueries
        .map(query => `
            <div class="recent-query-item" onclick="document.getElementById('query-input').value='${escapeHtml(query)}'; document.getElementById('send-btn').click();">
                ${query}
            </div>
        `)
        .join('');
}

// Network Status
function updateNetworkStatus() {
    const statusMap = {
        'online': { dot: 'online', text: 'ऑनलाइन' },
        'slow': { dot: 'slow', text: 'धीमा नेटवर्क' },
        'offline': { dot: 'offline', text: 'ऑफलाइन' }
    };
    
    const status = statusMap[state.networkSpeed];
    elements.statusDot.className = `status-dot ${status.dot}`;
    elements.statusText.textContent = status.text;
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, '&#39;');
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: Focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        elements.queryInput.focus();
    }
    
    // Ctrl/Cmd + D: Toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleTheme();
    }
});
