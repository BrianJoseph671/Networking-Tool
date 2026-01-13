// API Base URL
const API_BASE = '/api';

// Global state
let currentProspectId = null;
let currentResearchAgent = null;
let currentMessageId = null;

// ============== UTILITY FUNCTIONS ==============

function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = '<div class="loading"></div> Loading...';
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert('Success: ' + message);
}

// ============== TAB SWITCHING ==============

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Load data for the tab
    if (tabName === 'prospects') {
        loadProspects();
    } else if (tabName === 'research') {
        loadProspectsForResearch();
    } else if (tabName === 'messages') {
        loadProspectsForMessages();
    } else if (tabName === 'analytics') {
        loadAnalytics();
    }
}

// ============== PROSPECTS ==============

async function loadProspects() {
    showLoading('prospects-list');

    try {
        const response = await fetch(`${API_BASE}/prospects`);
        const prospects = await response.json();

        const listEl = document.getElementById('prospects-list');

        if (prospects.length === 0) {
            listEl.innerHTML = '<p class="text-gray-500">No prospects yet. Click "Add Prospect" to get started.</p>';
            return;
        }

        listEl.innerHTML = prospects.map(p => `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900">${p.name}</h3>
                        <p class="text-sm text-gray-600">${p.current_title || 'No title'} ${p.current_company ? 'at ' + p.current_company : ''}</p>
                        ${p.email ? `<p class="text-sm text-gray-500">${p.email}</p>` : ''}
                    </div>
                    <div class="flex gap-2">
                        ${!p.has_persona ?
                            `<button onclick="generatePersona(${p.id})" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                                Generate Persona
                            </button>` :
                            `<button onclick="viewPersona(${p.id})" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                                View Persona
                            </button>`
                        }
                    </div>
                </div>
                <div class="mt-2 flex gap-4 text-sm text-gray-500">
                    <span>📊 ${p.outreach_count} outreach(es)</span>
                    <span>📝 ${p.has_persona ? 'Persona ready' : 'No persona'}</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        showError('Failed to load prospects: ' + error.message);
    }
}

function showAddProspectModal() {
    document.getElementById('add-prospect-modal').classList.remove('hidden');
}

function hideAddProspectModal() {
    document.getElementById('add-prospect-modal').classList.add('hidden');
    // Clear inputs
    document.getElementById('prospect-name').value = '';
    document.getElementById('prospect-email').value = '';
    document.getElementById('prospect-linkedin').value = '';
    document.getElementById('prospect-company').value = '';
    document.getElementById('prospect-title').value = '';
}

async function addProspect() {
    const name = document.getElementById('prospect-name').value.trim();
    if (!name) {
        showError('Name is required');
        return;
    }

    const data = {
        name: name,
        email: document.getElementById('prospect-email').value.trim() || null,
        linkedin_url: document.getElementById('prospect-linkedin').value.trim() || null,
        current_company: document.getElementById('prospect-company').value.trim() || null,
        current_title: document.getElementById('prospect-title').value.trim() || null
    };

    try {
        const response = await fetch(`${API_BASE}/prospects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to add prospect');

        showSuccess('Prospect added successfully!');
        hideAddProspectModal();
        loadProspects();

    } catch (error) {
        showError('Failed to add prospect: ' + error.message);
    }
}

async function generatePersona(prospectId) {
    if (!confirm('Generate persona for this prospect? Make sure you have added research data first.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/prospects/${prospectId}/persona`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate persona');
        }

        const persona = await response.json();
        showSuccess('Persona generated successfully!');
        loadProspects();

    } catch (error) {
        showError('Failed to generate persona: ' + error.message);
    }
}

async function viewPersona(prospectId) {
    try {
        const response = await fetch(`${API_BASE}/prospects/${prospectId}/persona`);
        const persona = await response.json();

        alert(`Persona Summary:\n\n${persona.summary}\n\n` +
              `Expertise: ${persona.expertise_areas.join(', ')}\n\n` +
              `Communication Style: ${persona.communication_style}\n\n` +
              `Connection Strategy: ${persona.connection_strategy}`);

    } catch (error) {
        showError('Failed to load persona: ' + error.message);
    }
}

// ============== RESEARCH ==============

async function loadProspectsForResearch() {
    try {
        const response = await fetch(`${API_BASE}/prospects`);
        const prospects = await response.json();

        const select = document.getElementById('research-prospect-select');
        select.innerHTML = '<option value="">-- Select a prospect --</option>' +
            prospects.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

    } catch (error) {
        showError('Failed to load prospects: ' + error.message);
    }
}

function selectResearchAgent(agentType) {
    currentResearchAgent = agentType;

    const section = document.getElementById('research-input-section');
    section.classList.remove('hidden');

    const title = document.getElementById('research-agent-title');
    const agentNames = {
        'linkedin': 'LinkedIn Research Data',
        'google': 'Google/Web Research Data',
        'social_media': 'Social Media Research Data'
    };
    title.textContent = `Paste ${agentNames[agentType]}`;

    // Scroll to input section
    section.scrollIntoView({ behavior: 'smooth' });
}

async function submitResearch() {
    const prospectId = document.getElementById('research-prospect-select').value;
    const rawData = document.getElementById('research-data-input').value.trim();

    if (!prospectId) {
        showError('Please select a prospect');
        return;
    }

    if (!rawData) {
        showError('Please enter research data');
        return;
    }

    if (!currentResearchAgent) {
        showError('Please select a research agent');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/prospects/${prospectId}/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_type: currentResearchAgent,
                raw_text: rawData
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process research');
        }

        const result = await response.json();
        showSuccess('Research data processed successfully!');

        // Clear input
        document.getElementById('research-data-input').value = '';
        document.getElementById('research-input-section').classList.add('hidden');
        currentResearchAgent = null;

    } catch (error) {
        showError('Failed to process research: ' + error.message);
    }
}

// ============== MESSAGES ==============

async function loadProspectsForMessages() {
    try {
        const response = await fetch(`${API_BASE}/prospects`);
        const prospects = await response.json();

        const select = document.getElementById('message-prospect-select');
        select.innerHTML = '<option value="">-- Select a prospect --</option>' +
            prospects.map(p => `<option value="${p.id}" ${!p.has_persona ? 'disabled' : ''}>${p.name} ${!p.has_persona ? '(No persona)' : ''}</option>`).join('');

    } catch (error) {
        showError('Failed to load prospects: ' + error.message);
    }
}

async function loadPersona() {
    const prospectId = document.getElementById('message-prospect-select').value;
    if (!prospectId) {
        document.getElementById('persona-display').classList.add('hidden');
        return;
    }

    currentProspectId = prospectId;

    try {
        const response = await fetch(`${API_BASE}/prospects/${prospectId}/persona`);
        const persona = await response.json();

        document.getElementById('persona-summary').textContent = persona.summary;
        document.getElementById('persona-display').classList.remove('hidden');

    } catch (error) {
        showError('Failed to load persona: ' + error.message);
    }
}

async function generateMessage() {
    const prospectId = document.getElementById('message-prospect-select').value;
    if (!prospectId) {
        showError('Please select a prospect');
        return;
    }

    const data = {
        channel: document.getElementById('message-channel').value,
        tone: document.getElementById('message-tone').value,
        familiarity_level: document.getElementById('message-familiarity').value,
        degree_of_connection: parseInt(document.getElementById('message-degree').value),
        custom_context: document.getElementById('message-context').value.trim() || null
    };

    try {
        const response = await fetch(`${API_BASE}/prospects/${prospectId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate message');
        }

        const message = await response.json();
        currentMessageId = message.id;

        // Display message
        const messageDisplay = document.getElementById('generated-message');
        messageDisplay.classList.remove('hidden');

        if (message.subject) {
            document.getElementById('message-subject').innerHTML = `<strong>Subject:</strong> ${message.subject}`;
        } else {
            document.getElementById('message-subject').innerHTML = '';
        }

        document.getElementById('message-body').textContent = message.body;

        // Scroll to message
        messageDisplay.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        showError('Failed to generate message: ' + error.message);
    }
}

function copyMessage() {
    const body = document.getElementById('message-body').textContent;
    const subject = document.getElementById('message-subject').textContent;

    const fullMessage = subject ? `${subject}\n\n${body}` : body;

    navigator.clipboard.writeText(fullMessage).then(() => {
        showSuccess('Message copied to clipboard!');
    });
}

async function logOutreach() {
    if (!currentProspectId || !currentMessageId) {
        showError('No message to log');
        return;
    }

    const channel = document.getElementById('message-channel').value;

    try {
        const response = await fetch(`${API_BASE}/prospects/${currentProspectId}/outreach`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_id: currentMessageId,
                channel: channel,
                sent_at: new Date().toISOString()
            })
        });

        if (!response.ok) throw new Error('Failed to log outreach');

        showSuccess('Outreach logged successfully!');

        // Clear message display
        document.getElementById('generated-message').classList.add('hidden');
        currentMessageId = null;

    } catch (error) {
        showError('Failed to log outreach: ' + error.message);
    }
}

// ============== ANALYTICS ==============

async function loadAnalytics() {
    try {
        // Load performance metrics
        const perfResponse = await fetch(`${API_BASE}/analytics/performance`);
        const perfData = await perfResponse.json();

        // Load follow-ups
        const followUpResponse = await fetch(`${API_BASE}/analytics/follow-ups`);
        const followUpData = await followUpResponse.json();

        // Update stats
        if (perfData.overall_metrics) {
            document.getElementById('stat-total-sent').textContent = perfData.overall_metrics.total_sent || 0;
            document.getElementById('stat-response-rate').textContent =
                (perfData.overall_metrics.response_rate * 100).toFixed(1) + '%' || '0%';
        } else {
            document.getElementById('stat-total-sent').textContent = '0';
            document.getElementById('stat-response-rate').textContent = '0%';
        }

        document.getElementById('stat-follow-ups').textContent = followUpData.count || 0;

        // Display detailed analytics
        const detailsEl = document.getElementById('analytics-details');
        detailsEl.innerHTML = `
            <h3 class="font-semibold mb-4">Performance Insights</h3>
            ${perfData.top_insights ? `
                <div class="mb-4">
                    <h4 class="font-medium mb-2">Key Insights:</h4>
                    <ul class="list-disc list-inside space-y-1">
                        ${perfData.top_insights.map(insight => `<li class="text-gray-700">${insight}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${perfData.recommendations ? `
                <div class="mb-4">
                    <h4 class="font-medium mb-2">Recommendations:</h4>
                    <ul class="list-disc list-inside space-y-1">
                        ${perfData.recommendations.map(rec => `<li class="text-gray-700">${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${followUpData.follow_ups_needed && followUpData.follow_ups_needed.length > 0 ? `
                <div>
                    <h4 class="font-medium mb-2">Follow-ups Needed:</h4>
                    <ul class="space-y-2">
                        ${followUpData.follow_ups_needed.map(f => `
                            <li class="text-sm text-gray-700">
                                <strong>${f.prospect_name}</strong> via ${f.channel} - ${f.days_since_sent} days ago
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : '<p class="text-gray-500">No follow-ups needed at this time</p>'}
        `;

    } catch (error) {
        showError('Failed to load analytics: ' + error.message);
    }
}

// ============== INITIALIZATION ==============

document.addEventListener('DOMContentLoaded', () => {
    loadProspects();
});
