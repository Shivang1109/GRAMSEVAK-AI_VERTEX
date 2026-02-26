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
    totalBytesUsed: parseInt(localStorage.getItem('totalBytesUsed')) || 0,
    recentQueries: JSON.parse(localStorage.getItem('recentQueries')) || [],
    isOnline: navigator.onLine,
    networkSpeed: 'online', // online, slow, offline
    networkType: null, // 2g, 3g, 4g, or null
    userType: localStorage.getItem('userType') || null, // farmer, student, worker, or null
    userDistrict: localStorage.getItem('userDistrict') || null, // district name
    simulate2G: localStorage.getItem('simulate2G') === 'true' || false // 2G simulation mode
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
    toastContainer: document.getElementById('toast-container'),
    emergencyBtn: document.getElementById('emergency-btn'),
    simulate2GToggle: document.getElementById('simulate-2g-toggle')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initServiceWorker();
    initVoiceRecognition();
    initEventListeners();
    updateNetworkStatus();
    renderRecentQueries();
    
    // Check for first visit and show personalization
    checkFirstVisit();
    
    // Update network status periodically
    setInterval(updateNetworkStatus, 5000); // Check every 5 seconds
    
    // Listen for connection changes
    if ('connection' in navigator) {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (connection) {
            connection.addEventListener('change', updateNetworkStatus);
        }
    }
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

    // Emergency button
    if (elements.emergencyBtn) {
        elements.emergencyBtn.addEventListener('click', showEmergencyPanel);
    }
    
    // 2G Simulation toggle
    if (elements.simulate2GToggle) {
        // Set initial state
        elements.simulate2GToggle.checked = state.simulate2G;
        
        elements.simulate2GToggle.addEventListener('change', (e) => {
            state.simulate2G = e.target.checked;
            localStorage.setItem('simulate2G', state.simulate2G);
            
            if (state.simulate2G) {
                showToast('🐌 2G Mode सक्रिय - धीमी गति सिमुलेशन', 'warning');
            } else {
                showToast('✅ सामान्य मोड सक्रिय', 'success');
            }
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

    // Stop any ongoing speech
    stopSpeech();

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
            body: JSON.stringify({ 
                text: query,
                network_type: state.networkType,
                user_type: state.userType || 'general',
                simulate_2g: state.simulate2G || false
            })
        });
        
        const data = await response.json();
        const endTime = performance.now();
        const responseTime = Math.round(endTime - startTime);
        
        // Log compression info
        if (data.compressed) {
            console.log(`📦 Response compressed: ${data.original_length} → ${data.summary.length} chars`);
        }
        
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
    
    // Category emoji mapping
    const categoryEmojis = {
        'government_schemes': '🏛️',
        'agriculture': '🌾',
        'health': '🏥',
        'education': '📚',
        'financial': '💰',
        'legal': '⚖️',
        'disaster': '🚨',
        'livelihood': '💼',
        'general': '📋'
    };
    
    const categoryNames = {
        'government_schemes': 'योजना',
        'agriculture': 'खेती',
        'health': 'स्वास्थ्य',
        'education': 'शिक्षा',
        'financial': 'वित्त',
        'legal': 'कानूनी',
        'disaster': 'आपदा',
        'livelihood': 'रोजगार',
        'general': 'सामान्य'
    };
    
    const category = data.category || 'general';
    const categoryEmoji = categoryEmojis[category] || '📋';
    const categoryName = categoryNames[category] || 'सामान्य';
    
    // Check if emergency response
    const isEmergency = data.mode === 'emergency' || data.source === 'safety_filter';
    
    // Build structured response HTML
    let responseHTML = `
        <div class="response-header">
            <div class="response-scheme">
                <span>${isEmergency ? '🚨' : '📋'}</span>
                <span>${data.scheme_name || 'जानकारी'}</span>
            </div>
            <div class="response-badges">
                ${!isEmergency ? `<div class="response-badge category">${categoryEmoji} ${categoryName}</div>` : ''}
                <div class="response-badge mode ${isEmergency ? 'emergency' : ''}">${
                    isEmergency ? '🚨 आपातकाल' : 
                    data.mode === 'offline' ? '📴 ऑफलाइन' : '🤖 AI'
                }</div>
                ${data.simulate_2g_mode ? '<div class="response-badge simulate-2g">🐌 2G Mode</div>' : ''}
                ${data.low_confidence_warning ? '<div class="response-badge warning">⚠️ कम विश्वास</div>' : ''}
                ${data.fallback_mode ? '<div class="response-badge fallback">🔄 फॉलबैक</div>' : ''}
                ${data.compressed ? '<div class="response-badge compressed">📦 संकुचित</div>' : ''}
            </div>
        </div>
        <div class="response-body ${isEmergency ? 'emergency-body' : ''}">
            <div class="response-summary">${data.summary || data.answer}</div>
            ${!isEmergency && data.retrieval_method ? getRetrievalMethodBadge(data.retrieval_method, data.similarity_score) : ''}
            ${!isEmergency ? getFreshnessIndicator(data.last_updated, data.retrieval_method) : ''}
    `;
    
    // Add emergency helplines if available
    if (data.emergency_helplines && data.emergency_helplines.length > 0) {
        responseHTML += `
            <div class="response-section emergency-section">
                <div class="section-title">📞 आपातकालीन हेल्पलाइन</div>
                <div class="section-content">
                    <div class="helpline-list">
                        ${data.emergency_helplines.map(helpline => `
                            <div class="helpline-item">
                                <div class="helpline-name">${helpline.name}</div>
                                <div class="helpline-number">📞 ${helpline.number}</div>
                                <div class="helpline-desc">${helpline.description}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add eligibility if available
    if (data.eligibility) {
        responseHTML += `
            <div class="response-section">
                <div class="section-title">✅ पात्रता</div>
                <div class="section-content">${data.eligibility}</div>
            </div>
        `;
    }
    
    // Add documents if available
    if (data.documents_required && data.documents_required.length > 0) {
        responseHTML += `
            <div class="response-section">
                <div class="section-title">📄 आवश्यक दस्तावेज</div>
                <div class="section-content">
                    <ul class="doc-list">
                        ${data.documents_required.map(doc => `<li>${doc}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Add district-specific information if available
    if (state.userDistrict && state.userDistrict !== 'अन्य' && !isEmergency) {
        responseHTML += `
            <div class="response-section district-info">
                <div class="section-title">📍 स्थानीय जानकारी</div>
                <div class="section-content">आप ${state.userDistrict} जिले के नजदीकी CSC केंद्र या सरकारी कार्यालय से आवेदन कर सकते हैं।</div>
            </div>
        `;
    }
    
    responseHTML += `</div>`;
    
    // Add confidence indicator
    const confidenceLevel = data.confidence >= 0.7 ? 'high' : data.confidence >= 0.4 ? 'medium' : 'low';
    const confidenceText = confidenceLevel === 'high' ? 'उच्च' : confidenceLevel === 'medium' ? 'मध्यम' : 'कम';
    const confidenceColor = confidenceLevel === 'high' ? '#2e7d32' : confidenceLevel === 'medium' ? '#f57c00' : '#d32f2f';
    
    responseHTML += `
        <div class="response-confidence">
            <div class="confidence-label">विश्वास स्तर:</div>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${data.confidence * 100}%; background: ${confidenceColor}"></div>
            </div>
            <div class="confidence-text" style="color: ${confidenceColor}">${confidenceText} (${(data.confidence * 100).toFixed(0)}%)</div>
        </div>
    `;
    
    // Add footer with actions
    const answerText = data.summary || data.answer;
    const bytesSaved = CHATGPT_AVG_SIZE - (data.bytes_used || 2000);
    const percentSaved = ((bytesSaved / CHATGPT_AVG_SIZE) * 100).toFixed(1);
    
    // Generate unique ID for this response card
    const cardId = `response-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    responseHTML += `
        <div class="response-footer">
            <div class="response-actions">
                <button class="action-btn" onclick="copyAnswer('${escapeHtml(answerText)}')">
                    📋 कॉपी करें
                </button>
                <button class="action-btn" onclick="speakAnswer('${escapeHtml(answerText)}')">
                    🔊 सुनें
                </button>
                ${data.official_link ? `<button class="action-btn" onclick="window.open('${data.official_link}', '_blank')">🔗 आधिकारिक लिंक</button>` : ''}
                <button class="action-btn explain-btn" onclick="toggleExplainability('${cardId}')">
                    💡 यह उत्तर क्यों दिखाया गया?
                </button>
            </div>
            <div class="response-stats">
                <div class="stat-item">
                    <span>⏱️</span>
                    <span>${responseTime}ms</span>
                </div>
                <div class="stat-item">
                    <span>📊</span>
                    <span>${(data.bytes_used / 1024).toFixed(1)}KB</span>
                </div>
                <div class="stat-item savings">
                    <span>💾</span>
                    <span>${percentSaved}% बचत</span>
                </div>
            </div>
        </div>
        
        <!-- Feedback Section -->
        <div class="feedback-section" id="feedback-${cardId}">
            <div class="feedback-question">क्या यह उत्तर उपयोगी था?</div>
            <div class="feedback-buttons">
                <button class="feedback-btn helpful" onclick="submitFeedback('${cardId}', true)" id="helpful-${cardId}">
                    👍 हाँ
                </button>
                <button class="feedback-btn not-helpful" onclick="submitFeedback('${cardId}', false)" id="not-helpful-${cardId}">
                    👎 नहीं
                </button>
            </div>
            <div class="feedback-thanks hidden" id="thanks-${cardId}">
                ✅ धन्यवाद आपकी प्रतिक्रिया के लिए
            </div>
        </div>
        
        <!-- Explainability Panel -->
        <div id="explain-${cardId}" class="explainability-panel hidden">
            <div class="explain-header">
                <span class="explain-title">🔍 उत्तर विवरण</span>
                <button class="explain-close" onclick="toggleExplainability('${cardId}')">✕</button>
            </div>
            <div class="explain-content">
                <div class="explain-item">
                    <div class="explain-label">पहचाना गया विषय:</div>
                    <div class="explain-value">${categoryEmoji} ${categoryName} (${(data.category_confidence * 100).toFixed(0)}% विश्वास)</div>
                </div>
                <div class="explain-item">
                    <div class="explain-label">खोज विधि:</div>
                    <div class="explain-value">${getRetrievalMethodText(data.retrieval_method || 'semantic_match')}</div>
                </div>
                <div class="explain-item">
                    <div class="explain-label">उत्तर विश्वास स्तर:</div>
                    <div class="explain-value">
                        <div class="explain-confidence-bar">
                            <div class="explain-confidence-fill" style="width: ${(data.confidence * 100).toFixed(0)}%; background: ${getConfidenceColor(data.confidence)}"></div>
                        </div>
                        <span>${(data.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
                ${data.similarity_score ? `
                <div class="explain-item">
                    <div class="explain-label">समानता स्कोर:</div>
                    <div class="explain-value">${(data.similarity_score * 100).toFixed(0)}% मिलान</div>
                </div>
                ` : ''}
                <div class="explain-item">
                    <div class="explain-label">प्रतिक्रिया समय:</div>
                    <div class="explain-value">${responseTime}ms</div>
                </div>
                <div class="explain-item">
                    <div class="explain-label">डेटा उपयोग:</div>
                    <div class="explain-value">${(data.bytes_used / 1024).toFixed(2)}KB (${percentSaved}% बचत)</div>
                </div>
            </div>
            <div class="explain-footer">
                <span class="explain-disclaimer">⚙️ AI प्रणाली द्वारा निर्णय</span>
            </div>
        </div>
    `;
    
    card.innerHTML = responseHTML;
    
    // Store data for explainability
    card.dataset.explainData = JSON.stringify({
        category: data.category,
        categoryConfidence: data.category_confidence,
        retrievalMethod: data.retrieval_method,
        confidence: data.confidence,
        similarityScore: data.similarity_score,
        responseTime: responseTime,
        bytesUsed: data.bytes_used
    });
    
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

// Get retrieval method badge HTML
function getRetrievalMethodBadge(method, score) {
    const badges = {
        'direct_match': {
            icon: '🟢',
            text: 'Direct Knowledge Match',
            textHi: 'सीधा ज्ञान मिलान',
            color: '#2e7d32',
            bgColor: '#e8f5e9'
        },
        'semantic_match': {
            icon: '🟡',
            text: 'Semantic Retrieval',
            textHi: 'अर्थ-आधारित खोज',
            color: '#f57c00',
            bgColor: '#fff3e0'
        },
        'rag_llm': {
            icon: '🔵',
            text: 'AI-Generated (RAG Assisted)',
            textHi: 'AI-जनित (RAG सहायता)',
            color: '#1976d2',
            bgColor: '#e3f2fd'
        }
    };
    
    const badge = badges[method] || badges['semantic_match'];
    const scorePercent = score ? Math.round(score * 100) : 0;
    
    return `
        <div class="retrieval-method-badge" style="background: ${badge.bgColor}; border-left: 3px solid ${badge.color};">
            <div class="retrieval-badge-content">
                <span class="retrieval-icon">${badge.icon}</span>
                <div class="retrieval-info">
                    <div class="retrieval-text" style="color: ${badge.color};">${badge.textHi}</div>
                    ${score ? `<div class="retrieval-score">Similarity: ${scorePercent}%</div>` : ''}
                </div>
            </div>
        </div>
    `;
}

// Get freshness indicator HTML
function getFreshnessIndicator(lastUpdated, retrievalMethod) {
    if (retrievalMethod === 'rag_llm' || !lastUpdated) {
        // LLM-generated or no date available
        return `
            <div class="freshness-indicator llm-generated">
                <span class="freshness-icon">🤖</span>
                <span class="freshness-text">संदर्भ आधारित उत्तर</span>
            </div>
        `;
    }
    
    // Format date to readable format
    const date = new Date(lastUpdated);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthName = months[date.getMonth()];
    const year = date.getFullYear();
    const formattedDate = `${monthName} ${year}`;
    
    // Calculate age in days
    const now = new Date();
    const ageInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    // Determine freshness level
    let freshnessClass = 'fresh';
    let freshnessIcon = '🟢';
    
    if (ageInDays > 365) {
        freshnessClass = 'old';
        freshnessIcon = '🟡';
    } else if (ageInDays > 180) {
        freshnessClass = 'moderate';
        freshnessIcon = '🟢';
    }
    
    return `
        <div class="freshness-indicator ${freshnessClass}">
            <span class="freshness-icon">${freshnessIcon}</span>
            <span class="freshness-text">अंतिम अपडेट: ${formattedDate}</span>
        </div>
    `;
}

// Get retrieval method text for explainability
function getRetrievalMethodText(method) {
    const methods = {
        'direct_match': '🟢 सीधा ज्ञान मिलान (Direct Match)',
        'semantic_match': '🟡 अर्थ-आधारित खोज (Semantic Search)',
        'rag_llm': '🔵 AI-जनित उत्तर (RAG Assisted)'
    };
    return methods[method] || methods['semantic_match'];
}

// Get confidence color
function getConfidenceColor(confidence) {
    if (confidence >= 0.7) return '#2e7d32'; // Green
    if (confidence >= 0.4) return '#f57c00'; // Orange
    return '#d32f2f'; // Red
}

// Toggle explainability panel
window.toggleExplainability = function(cardId) {
    const panel = document.getElementById(`explain-${cardId}`);
    if (!panel) return;
    
    if (panel.classList.contains('hidden')) {
        // Show panel
        panel.classList.remove('hidden');
        panel.style.maxHeight = panel.scrollHeight + 'px';
        
        // Scroll into view
        setTimeout(() => {
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    } else {
        // Hide panel
        panel.style.maxHeight = '0';
        setTimeout(() => {
            panel.classList.add('hidden');
        }, 300);
    }
};

// Submit Feedback
window.submitFeedback = async function(cardId, isHelpful) {
    // Check if already voted
    const votedResponses = JSON.parse(localStorage.getItem('votedResponses') || '[]');
    
    if (votedResponses.includes(cardId)) {
        showToast('आपने पहले ही वोट दिया है', 'warning');
        return;
    }
    
    // Disable buttons
    const helpfulBtn = document.getElementById(`helpful-${cardId}`);
    const notHelpfulBtn = document.getElementById(`not-helpful-${cardId}`);
    const thanksMsg = document.getElementById(`thanks-${cardId}`);
    
    if (helpfulBtn) helpfulBtn.disabled = true;
    if (notHelpfulBtn) notHelpfulBtn.disabled = true;
    
    try {
        // Send feedback to backend
        const response = await fetch(`${API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                response_id: cardId,
                is_helpful: isHelpful,
                category: state.currentCategory
            })
        });
        
        if (response.ok) {
            // Mark as voted
            votedResponses.push(cardId);
            localStorage.setItem('votedResponses', JSON.stringify(votedResponses));
            
            // Hide buttons, show thanks
            if (helpfulBtn) helpfulBtn.style.display = 'none';
            if (notHelpfulBtn) notHelpfulBtn.style.display = 'none';
            if (thanksMsg) {
                thanksMsg.classList.remove('hidden');
                thanksMsg.style.display = 'block';
            }
            
            showToast('धन्यवाद आपकी प्रतिक्रिया के लिए', 'success');
        } else {
            throw new Error('Feedback submission failed');
        }
    } catch (error) {
        console.error('Feedback error:', error);
        // Still mark as voted locally to prevent spam
        votedResponses.push(cardId);
        localStorage.setItem('votedResponses', JSON.stringify(votedResponses));
        
        // Show thanks message anyway
        if (helpfulBtn) helpfulBtn.style.display = 'none';
        if (notHelpfulBtn) notHelpfulBtn.style.display = 'none';
        if (thanksMsg) {
            thanksMsg.classList.remove('hidden');
            thanksMsg.style.display = 'block';
        }
        
        showToast('धन्यवाद आपकी प्रतिक्रिया के लिए', 'success');
    }
};

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
    // Detect network type using Network Information API
    if ('connection' in navigator) {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (connection && connection.effectiveType) {
            const effectiveType = connection.effectiveType;
            
            // Map effective type to our categories
            if (effectiveType === 'slow-2g' || effectiveType === '2g') {
                state.networkType = '2g';
                state.networkSpeed = 'slow';
            } else if (effectiveType === '3g') {
                state.networkType = '3g';
                state.networkSpeed = 'slow';
            } else if (effectiveType === '4g') {
                state.networkType = '4g';
                state.networkSpeed = 'online';
            } else {
                state.networkType = null;
                state.networkSpeed = 'online';
            }
            
            console.log(`📡 Network detected: ${effectiveType} (mapped to: ${state.networkType})`);
        }
    }
    
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

// Copy Answer Function
function copyAnswer(text) {
    // Unescape HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    const cleanText = textarea.value;
    
    navigator.clipboard.writeText(cleanText).then(() => {
        showToast('उत्तर कॉपी हो गया', 'success');
    }).catch(err => {
        console.error('Copy failed:', err);
        showToast('कॉपी करने में त्रुटि', 'error');
    });
}

// Text-to-Speech Function
let currentSpeech = null;

function speakAnswer(text) {
    // Stop any ongoing speech
    if (currentSpeech) {
        window.speechSynthesis.cancel();
        currentSpeech = null;
    }
    
    // Check if browser supports speech synthesis
    if (!('speechSynthesis' in window)) {
        showToast('आपका ब्राउज़र TTS सपोर्ट नहीं करता', 'error');
        return;
    }
    
    // Unescape HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    const cleanText = textarea.value;
    
    // Create speech utterance
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'hi-IN'; // Hindi language
    utterance.rate = 0.9; // Slightly slower for clarity
    utterance.pitch = 1.0;
    
    // Event handlers
    utterance.onstart = () => {
        currentSpeech = utterance;
        showToast('बोल रहा है...', 'info');
    };
    
    utterance.onend = () => {
        currentSpeech = null;
    };
    
    utterance.onerror = (event) => {
        console.error('Speech error:', event);
        currentSpeech = null;
        showToast('बोलने में त्रुटि', 'error');
    };
    
    // Speak
    window.speechSynthesis.speak(utterance);
}

// Stop speech when new query is submitted
function stopSpeech() {
    if (currentSpeech) {
        window.speechSynthesis.cancel();
        currentSpeech = null;
    }
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

// ============================================================================
// BANDWIDTH COUNTER & ANIMATION
// ============================================================================

function updateBandwidthStats(bytesUsed) {
    // Update state
    state.totalBytesUsed += bytesUsed;
    const bytesSaved = CHATGPT_AVG_SIZE - bytesUsed;
    state.totalBytesSaved += bytesSaved;
    
    // Save to localStorage
    localStorage.setItem('totalBytesUsed', state.totalBytesUsed);
    localStorage.setItem('totalBytesSaved', state.totalBytesSaved);
    localStorage.setItem('totalQueries', state.totalQueries);
}

function showBandwidthPanel(bytesUsed) {
    const panel = elements.bandwidthPanel;
    
    // Calculate metrics
    const kbUsed = (bytesUsed / 1024).toFixed(2);
    const percentSaved = (((CHATGPT_AVG_SIZE - bytesUsed) / CHATGPT_AVG_SIZE) * 100).toFixed(1);
    const totalKbUsed = (state.totalBytesUsed / 1024).toFixed(1);
    const totalKbSaved = (state.totalBytesSaved / 1024).toFixed(1);
    
    // Update panel content
    panel.innerHTML = `
        <div class="bandwidth-header">
            <h3>📊 बैंडविड्थ डैशबोर्ड</h3>
            <button id="bandwidth-close" class="close-btn">✕</button>
        </div>
        <div class="bandwidth-content">
            <div class="bandwidth-stat">
                <div class="stat-label">इस प्रश्न में</div>
                <div class="stat-value animate-number" data-value="${kbUsed}">${kbUsed} KB</div>
                <div class="stat-sublabel">उपयोग हुआ</div>
            </div>
            <div class="bandwidth-stat highlight">
                <div class="stat-label">बचत</div>
                <div class="stat-value large animate-number" data-value="${percentSaved}">${percentSaved}%</div>
                <div class="stat-sublabel">ChatGPT की तुलना में</div>
            </div>
            <div class="bandwidth-divider"></div>
            <div class="bandwidth-stat">
                <div class="stat-label">कुल उपयोग</div>
                <div class="stat-value animate-number" data-value="${totalKbUsed}">${totalKbUsed} KB</div>
                <div class="stat-sublabel">${state.totalQueries} प्रश्नों में</div>
            </div>
            <div class="bandwidth-stat highlight">
                <div class="stat-label">कुल बचत</div>
                <div class="stat-value large animate-number" data-value="${totalKbSaved}">${totalKbSaved} KB</div>
                <div class="stat-sublabel">≈ ${(totalKbSaved / 1024).toFixed(1)} MB</div>
            </div>
        </div>
        <div class="bandwidth-footer">
            <div class="bandwidth-comparison">
                <div class="comparison-item">
                    <span class="comparison-label">GramSevak AI:</span>
                    <span class="comparison-value">${kbUsed} KB</span>
                </div>
                <div class="comparison-item">
                    <span class="comparison-label">ChatGPT:</span>
                    <span class="comparison-value">~45 KB</span>
                </div>
            </div>
        </div>
    `;
    
    // Show panel
    panel.classList.remove('hidden');
    
    // Animate numbers
    animateNumbers();
    
    // Re-attach close button event
    document.getElementById('bandwidth-close').addEventListener('click', () => {
        panel.classList.add('hidden');
    });
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (!panel.classList.contains('hidden')) {
            panel.classList.add('hidden');
        }
    }, 10000);
}

function animateNumbers() {
    const elements = document.querySelectorAll('.animate-number');
    
    elements.forEach(el => {
        const target = parseFloat(el.dataset.value);
        const duration = 1000; // 1 second
        const steps = 30;
        const increment = target / steps;
        let current = 0;
        let step = 0;
        
        const timer = setInterval(() => {
            step++;
            current += increment;
            
            if (step >= steps) {
                current = target;
                clearInterval(timer);
            }
            
            // Format based on value
            if (target < 10) {
                el.textContent = current.toFixed(2);
            } else if (target < 100) {
                el.textContent = current.toFixed(1);
            } else {
                el.textContent = Math.round(current);
            }
        }, duration / steps);
    });
}

// ============================================================================
// LOCAL PERSONALIZATION
// ============================================================================

function checkFirstVisit() {
    // Check if user type is already set
    if (!state.userType) {
        // Show personalization modal after a short delay
        setTimeout(showPersonalizationModal, 1000);
    } else {
        // Update suggested prompts based on user type
        updateSuggestedPrompts();
    }
}

function showPersonalizationModal() {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'personalization-modal';
    modal.id = 'personalization-modal';
    modal.innerHTML = `
        <div class="modal-overlay"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2>👋 नमस्ते!</h2>
                <p>आप कौन हैं? हम आपके लिए बेहतर सुझाव दे सकते हैं।</p>
            </div>
            <div class="modal-body">
                <div class="user-type-options">
                    <button class="user-type-btn" data-type="farmer">
                        <span class="user-type-icon">🌾</span>
                        <span class="user-type-label">किसान</span>
                        <span class="user-type-desc">खेती, फसल, योजनाएं</span>
                    </button>
                    <button class="user-type-btn" data-type="student">
                        <span class="user-type-icon">📚</span>
                        <span class="user-type-label">छात्र</span>
                        <span class="user-type-desc">शिक्षा, छात्रवृत्ति</span>
                    </button>
                    <button class="user-type-btn" data-type="worker">
                        <span class="user-type-icon">💼</span>
                        <span class="user-type-label">कामगार</span>
                        <span class="user-type-desc">रोजगार, कौशल</span>
                    </button>
                    <button class="user-type-btn" data-type="general">
                        <span class="user-type-icon">👤</span>
                        <span class="user-type-label">सामान्य</span>
                        <span class="user-type-desc">सभी जानकारी</span>
                    </button>
                </div>
            </div>
            <div class="modal-footer">
                <button class="skip-btn" onclick="skipPersonalization()">बाद में</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners to user type buttons
    const userTypeBtns = modal.querySelectorAll('.user-type-btn');
    userTypeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const userType = btn.dataset.type;
            // Show district selection after user type
            showDistrictSelection(userType);
        });
    });
}

function showDistrictSelection(userType) {
    const modal = document.getElementById('personalization-modal');
    if (!modal) return;
    
    // List of major districts in India (sample - can be expanded)
    const districts = [
        'आगरा', 'अलीगढ़', 'इलाहाबाद', 'कानपुर', 'लखनऊ', 'मेरठ', 'वाराणसी',
        'गाजियाबाद', 'नोएडा', 'गोरखपुर', 'बरेली', 'मुरादाबाद', 'सहारनपुर',
        'जयपुर', 'जोधपुर', 'कोटा', 'उदयपुर', 'अजमेर', 'बीकानेर',
        'पटना', 'गया', 'भागलपुर', 'मुजफ्फरपुर', 'दरभंगा',
        'भोपाल', 'इंदौर', 'जबलपुर', 'ग्वालियर', 'उज्जैन',
        'रायपुर', 'बिलासपुर', 'दुर्ग', 'भिलाई',
        'अन्य'
    ];
    
    modal.querySelector('.modal-content').innerHTML = `
        <div class="modal-header">
            <h2>📍 आपका जिला</h2>
            <p>अपना जिला चुनें (बेहतर स्थानीय जानकारी के लिए)</p>
        </div>
        <div class="modal-body">
            <div class="district-search">
                <input type="text" id="district-search" placeholder="🔍 जिला खोजें..." class="district-input">
            </div>
            <div class="district-list" id="district-list">
                ${districts.map(district => `
                    <button class="district-btn" data-district="${district}">${district}</button>
                `).join('')}
            </div>
        </div>
        <div class="modal-footer">
            <button class="skip-btn" onclick="skipDistrictSelection('${userType}')">छोड़ें</button>
        </div>
    `;
    
    // Add search functionality
    const searchInput = document.getElementById('district-search');
    const districtBtns = modal.querySelectorAll('.district-btn');
    
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        districtBtns.forEach(btn => {
            const district = btn.dataset.district.toLowerCase();
            if (district.includes(searchTerm)) {
                btn.style.display = 'block';
            } else {
                btn.style.display = 'none';
            }
        });
    });
    
    // Add event listeners to district buttons
    districtBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const district = btn.dataset.district;
            setUserTypeAndDistrict(userType, district);
            modal.remove();
        });
    });
}

function setUserTypeAndDistrict(userType, district) {
    state.userType = userType;
    state.userDistrict = district;
    localStorage.setItem('userType', userType);
    localStorage.setItem('userDistrict', district);
    
    // Update suggested prompts
    updateSuggestedPrompts();
    
    // Show success message
    const userTypeNames = {
        farmer: 'किसान',
        student: 'छात्र',
        worker: 'कामगार',
        general: 'सामान्य'
    };
    
    showToast(`${userTypeNames[userType]} (${district}) के लिए तैयार`, 'success');
}

function skipDistrictSelection(userType) {
    setUserType(userType);
    const modal = document.getElementById('personalization-modal');
    if (modal) {
        modal.remove();
    }
}

function setUserType(userType) {
    state.userType = userType;
    localStorage.setItem('userType', userType);
    
    // Update suggested prompts
    updateSuggestedPrompts();
    
    // Show success message
    const userTypeNames = {
        farmer: 'किसान',
        student: 'छात्र',
        worker: 'कामगार',
        general: 'सामान्य'
    };
    
    showToast(`${userTypeNames[userType]} के लिए सुझाव तैयार हैं`, 'success');
}

function skipPersonalization() {
    const modal = document.querySelector('.personalization-modal');
    if (modal) {
        modal.remove();
    }
}

function updateSuggestedPrompts() {
    const promptsContainer = document.querySelector('.suggested-prompts');
    if (!promptsContainer) return;
    
    // Define prompts for each user type
    const promptsByType = {
        farmer: [
            { icon: '💰', text: 'PM-KISAN योजना क्या है?', query: 'पीएम किसान योजना में कितने पैसे मिलते हैं?' },
            { icon: '🌾', text: 'फसल बीमा कैसे लें?', query: 'फसल बीमा में कितना प्रीमियम देना होता है?' },
            { icon: '🚜', text: 'खेती में सब्सिडी', query: 'सोलर पंप पर कितनी सब्सिडी मिलती है?' },
            { icon: '🌱', text: 'बीज और खाद योजना', query: 'बीज और खाद पर सब्सिडी कैसे मिलेगी?' }
        ],
        student: [
            { icon: '📚', text: 'छात्रवृत्ति कैसे मिलेगी?', query: 'छात्रवृत्ति के लिए कैसे आवेदन करें?' },
            { icon: '🎓', text: '12वीं के बाद क्या करें?', query: '12वीं के बाद कौन सा कोर्स करें?' },
            { icon: '💻', text: 'मुफ्त कंप्यूटर कोर्स', query: 'मुफ्त कंप्यूटर प्रशिक्षण कहां मिलेगा?' },
            { icon: '📖', text: 'ऑनलाइन पढ़ाई', query: 'ऑनलाइन पढ़ाई के लिए क्या करें?' }
        ],
        worker: [
            { icon: '💼', text: 'MGNREGA में काम', query: 'मनरेगा में काम कैसे मिलता है?' },
            { icon: '🔧', text: 'कौशल विकास योजना', query: 'कौशल विकास योजना में क्या सिखाते हैं?' },
            { icon: '🏭', text: 'छोटा व्यवसाय शुरू करें', query: 'छोटा व्यवसाय शुरू करने के लिए लोन कैसे मिलेगा?' },
            { icon: '💰', text: 'मुद्रा लोन', query: 'मुद्रा लोन कैसे मिलता है?' }
        ],
        general: [
            { icon: '💰', text: 'PM-KISAN योजना', query: 'पीएम किसान योजना में कितने पैसे मिलते हैं?' },
            { icon: '🏥', text: 'आयुष्मान भारत', query: 'आयुष्मान भारत योजना में कितना इलाज मुफ्त है?' },
            { icon: '🏠', text: 'आवास योजना', query: 'प्रधानमंत्री आवास योजना में कितनी सहायता मिलती है?' },
            { icon: '💳', text: 'जन धन खाता', query: 'जन धन खाता कैसे खोलें?' }
        ]
    };
    
    const prompts = promptsByType[state.userType] || promptsByType.general;
    
    // Update prompt cards
    promptsContainer.innerHTML = prompts.map(prompt => `
        <div class="prompt-card" data-query="${prompt.query}">
            <div class="prompt-icon">${prompt.icon}</div>
            <div class="prompt-text">${prompt.text}</div>
        </div>
    `).join('');
    
    // Re-attach event listeners
    const promptCards = promptsContainer.querySelectorAll('.prompt-card');
    promptCards.forEach(card => {
        card.addEventListener('click', () => {
            const query = card.dataset.query;
            elements.queryInput.value = query;
            handleQuery();
        });
    });
}


// ============================================================================
// EMERGENCY MODE
// ============================================================================

function showEmergencyPanel() {
    // Emergency helplines data (works offline)
    const emergencyHelplines = [
        {
            name: 'एम्बुलेंस',
            number: '108',
            description: 'चिकित्सा आपातकाल के लिए'
        },
        {
            name: 'पुलिस',
            number: '100',
            description: 'कानून व्यवस्था के लिए'
        },
        {
            name: 'महिला हेल्पलाइन',
            number: '181',
            description: 'महिलाओं की सहायता के लिए'
        },
        {
            name: 'बाल हेल्पलाइन',
            number: '1098',
            description: 'बच्चों की सुरक्षा के लिए'
        },
        {
            name: 'आपदा प्रबंधन',
            number: '112',
            description: 'सभी आपातकालीन सेवाएं'
        },
        {
            name: 'फायर ब्रिगेड',
            number: '101',
            description: 'आग लगने पर'
        }
    ];
    
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'emergency-overlay';
    overlay.id = 'emergency-overlay';
    
    // Create panel
    const panel = document.createElement('div');
    panel.className = 'emergency-panel';
    panel.id = 'emergency-panel';
    
    panel.innerHTML = `
        <div class="emergency-panel-header">
            <h2>🚨 आपातकालीन सहायता</h2>
            <p>तुरंत मदद के लिए नीचे दिए गए नंबर पर कॉल करें</p>
        </div>
        <div class="emergency-panel-body">
            ${emergencyHelplines.map(helpline => `
                <div class="emergency-helpline-item">
                    <div class="emergency-helpline-info">
                        <div class="emergency-helpline-name">${helpline.name}</div>
                        <div class="emergency-helpline-desc">${helpline.description}</div>
                    </div>
                    <a href="tel:${helpline.number}" class="emergency-helpline-number">${helpline.number}</a>
                </div>
            `).join('')}
        </div>
        <div class="emergency-panel-footer">
            <button class="emergency-close-btn" onclick="closeEmergencyPanel()">बंद करें</button>
        </div>
    `;
    
    // Add to DOM
    document.body.appendChild(overlay);
    document.body.appendChild(panel);
    
    // Close on overlay click
    overlay.addEventListener('click', closeEmergencyPanel);
    
    // Show toast
    showToast('आपातकालीन नंबर (ऑफलाइन उपलब्ध)', 'warning');
}

window.closeEmergencyPanel = function() {
    const overlay = document.getElementById('emergency-overlay');
    const panel = document.getElementById('emergency-panel');
    
    if (overlay) overlay.remove();
    if (panel) panel.remove();
};
