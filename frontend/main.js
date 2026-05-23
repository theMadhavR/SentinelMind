/**
 * Adaptive Cybersecurity System - Frontend JavaScript
 * Real-time behavior monitoring and anomaly detection dashboard
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000';
let authToken = null;
let currentUser = null;
let sessionStartTime = null;
let actionCount = 0;
let behaviorChart = null;
let alertCheckInterval = null;
let updateInterval = null;
let recentActions = [];

// DOM Elements
const loginSection = document.getElementById('loginSection');
const dashboardSection = document.getElementById('dashboardSection');
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');
const logoutBtn = document.getElementById('logoutBtn');
const usernameDisplay = document.getElementById('username');
const currentTimeDisplay = document.getElementById('currentTime');
const systemStatusDisplay = document.getElementById('systemStatus');
const refreshDataBtn = document.getElementById('refreshData');

// Dashboard Elements
const riskLevelEl = document.getElementById('riskLevel');
const riskCard = document.querySelector('#riskCard .stat-icon');
const anomalyScoreEl = document.getElementById('anomalyScore');
const activeAlertsEl = document.getElementById('activeAlerts');
const sessionDurationEl = document.getElementById('sessionDuration');
const actionCountEl = document.getElementById('actionCount');
const recentActionsList = document.getElementById('recentActionsList');
const alertsList = document.getElementById('alertsList');
const alertBadge = document.getElementById('alertBadge');
const profileConfidenceEl = document.getElementById('profileConfidence');
const normalHoursEl = document.getElementById('normalHours');
const avgSessionEl = document.getElementById('avgSession');
const commonActionsEl = document.getElementById('commonActions');
const devicePatternEl = document.getElementById('devicePattern');
const meterFill = document.getElementById('meterFill');
const meterIndicator = document.getElementById('meterIndicator');
const detectionDetails = document.getElementById('detectionDetails');

// Modals
const alertModal = document.getElementById('alertModal');
const forceLogoutModal = document.getElementById('forceLogoutModal');
const simulationPanel = document.getElementById('simulationPanel');
const simulateAttackBtn = document.getElementById('simulateAttackBtn');
const closeSimulationBtn = document.getElementById('closeSimulationBtn');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Check for saved token
    const savedToken = localStorage.getItem('cybersecurity_token');
    const savedUser = localStorage.getItem('cybersecurity_user');
    
    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        initializeDashboard();
    }
    
    // Update current time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize empty charts
    initializeCharts();
});

function setupEventListeners() {
    // Login/Register
    loginBtn.addEventListener('click', handleLogin);
    registerBtn.addEventListener('click', handleRegister);
    logoutBtn.addEventListener('click', handleLogout);
    
    // Enter key for login
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    
    // Action buttons
    document.querySelectorAll('.action-btn[data-action]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.closest('.action-btn').dataset.action;
            performUserAction(action);
        });
    });
    
    // Simulation
    simulateAttackBtn.addEventListener('click', () => {
        simulationPanel.style.display = 'block';
    });
    
    closeSimulationBtn.addEventListener('click', () => {
        simulationPanel.style.display = 'none';
        document.getElementById('simulationResults').style.display = 'none';
    });
    
    // Simulation buttons
    document.querySelectorAll('.btn-simulate').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const type = e.target.closest('.btn-simulate').dataset.type;
            simulateAttack(type);
        });
    });
    
    // Refresh data
    refreshDataBtn.addEventListener('click', refreshDashboardData);
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });
    
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Alert modal buttons
    document.getElementById('acknowledgeAlert').addEventListener('click', () => {
        alertModal.style.display = 'none';
    });
    
    document.getElementById('viewDetails').addEventListener('click', () => {
        alertModal.style.display = 'none';
        // In a real app, navigate to detailed view
        showNotification('Viewing alert details...', 'info');
    });
    
    // Force logout modal
    document.getElementById('okLogout').addEventListener('click', () => {
        forceLogoutModal.style.display = 'none';
        handleLogout();
    });
}

function updateCurrentTime() {
    const now = new Date();
    currentTimeDisplay.textContent = now.toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

async function handleLogin() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    
    if (!username || !password) {
        showNotification('Please enter both username and password', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Save token and user info
            authToken = data.token;
            currentUser = {
                id: data.user_id,
                username: data.username,
                login_id: data.login_id
            };
            
            localStorage.setItem('cybersecurity_token', authToken);
            localStorage.setItem('cybersecurity_user', JSON.stringify(currentUser));
            
            // Initialize dashboard
            initializeDashboard();
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please check if backend is running.', 'error');
        console.error('Login error:', error);
    }
}

async function handleRegister() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    const email = `${username}@example.com`; // For demo purposes
    
    if (!username || !password) {
        showNotification('Please enter both username and password', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Registration successful! You can now login.', 'success');
        } else {
            showNotification(data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please check if backend is running.', 'error');
        console.error('Registration error:', error);
    }
}

function handleLogout() {
    // Clear stored data
    localStorage.removeItem('cybersecurity_token');
    localStorage.removeItem('cybersecurity_user');
    
    // Stop intervals
    if (alertCheckInterval) clearInterval(alertCheckInterval);
    if (updateInterval) clearInterval(updateInterval);
    
    // Reset state
    authToken = null;
    currentUser = null;
    sessionStartTime = null;
    actionCount = 0;
    recentActions = [];
    
    // Show login screen
    loginSection.style.display = 'block';
    dashboardSection.style.display = 'none';
    logoutBtn.style.display = 'none';
    usernameDisplay.textContent = 'Not logged in';
    
    showNotification('Logged out successfully', 'info');
}

function initializeDashboard() {
    // Hide login, show dashboard
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'block';
    logoutBtn.style.display = 'flex';
    
    // Update user display
    usernameDisplay.textContent = currentUser.username;
    
    // Start session timer
    sessionStartTime = new Date();
    updateSessionTimer();
    
    // Load initial data
    loadDashboardData();
    loadUserBehavior();
    loadSecurityAlerts();
    
    // Start periodic updates
    alertCheckInterval = setInterval(checkForAnomalies, 10000); // Every 10 seconds
    updateInterval = setInterval(updateDashboard, 30000); // Every 30 seconds
    
    // Show welcome message
    setTimeout(() => {
        showNotification('Welcome to Adaptive Cybersecurity System! System is monitoring your behavior.', 'info');
    }, 1000);
}

function updateSessionTimer() {
    if (!sessionStartTime) return;
    
    const now = new Date();
    const diff = Math.floor((now - sessionStartTime) / 1000);
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    
    sessionDurationEl.textContent = `${minutes}m ${seconds}s`;
    
    // Update every second
    setTimeout(updateSessionTimer, 1000);
}

async function loadDashboardData() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateDashboardStats(data);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateDashboardStats(data) {
    // Update risk level
    riskLevelEl.textContent = data.risk_level;
    riskLevelEl.className = `stat-value text-${data.risk_level.toLowerCase()}`;
    
    // Update risk card color
    riskCard.className = 'stat-icon';
    if (data.risk_level === 'HIGH') {
        riskCard.classList.add('risk-high');
    } else if (data.risk_level === 'MEDIUM') {
        riskCard.classList.add('risk-medium');
    } else {
        riskCard.classList.add('risk-low');
    }
    
    // Update anomaly score
    const score = data.anomaly_score || 0;
    anomalyScoreEl.textContent = score.toFixed(2);
    anomalyScoreEl.className = `stat-value ${score > 0.7 ? 'text-danger' : score > 0.4 ? 'text-warning' : 'text-success'}`;
    
    // Update meter
    updateAnomalyMeter(score);
    
    // Update active alerts
    const alertCount = data.recent_alerts?.filter(a => a.status === 'active').length || 0;
    activeAlertsEl.textContent = alertCount;
    
    // Update detection details
    updateDetectionDetails(data);
}

function updateAnomalyMeter(score) {
    const percentage = Math.min(score * 100, 100);
    
    // Update meter fill (showing normal area)
    meterFill.style.width = `${100 - percentage}%`;
    
    // Update indicator position
    meterIndicator.style.left = `${percentage}%`;
    meterIndicator.querySelector('.indicator-value').textContent = score.toFixed(2);
    
    // Update indicator color based on risk
    const indicatorDot = meterIndicator.querySelector('.indicator-dot');
    indicatorDot.style.borderColor = score > 0.7 ? '#ef4444' : score > 0.4 ? '#f59e0b' : '#10b981';
}

function updateDetectionDetails(data) {
    const score = data.anomaly_score || 0;
    let detailsHTML = '';
    
    if (score > 0.9) {
        detailsHTML = `
            <div class="alert-item high">
                <div class="alert-header-small">
                    <span class="alert-title">CRITICAL ANOMALY DETECTED</span>
                    <span class="alert-time">Just now</span>
                </div>
                <p class="alert-message">High-risk behavior pattern detected. Immediate action recommended.</p>
                <div class="alert-score">Score: ${score.toFixed(2)}</div>
            </div>
        `;
    } else if (score > 0.7) {
        detailsHTML = `
            <div class="alert-item medium">
                <div class="alert-header-small">
                    <span class="alert-title">SUSPICIOUS BEHAVIOR</span>
                    <span class="alert-time">Just now</span>
                </div>
                <p class="alert-message">Unusual activity detected. System is monitoring closely.</p>
                <div class="alert-score">Score: ${score.toFixed(2)}</div>
            </div>
        `;
    } else if (score > 0.4) {
        detailsHTML = `
            <p><i class="fas fa-info-circle text-warning"></i> Minor deviations detected. No immediate action required.</p>
            <p class="small">Score: ${score.toFixed(2)}</p>
        `;
    } else {
        detailsHTML = `
            <p><i class="fas fa-check-circle text-success"></i> Behavior appears normal. System is monitoring patterns.</p>
            <p class="small">Score: ${score.toFixed(2)}</p>
        `;
    }
    
    detectionDetails.innerHTML = detailsHTML;
}

async function loadUserBehavior() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/user/behavior`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateBehaviorProfile(data);
        }
    } catch (error) {
        console.error('Error loading behavior data:', error);
    }
}

function updateBehaviorProfile(data) {
    if (!data.profile) {
        profileConfidenceEl.textContent = '0%';
        normalHoursEl.textContent = 'Not enough data';
        avgSessionEl.textContent = 'N/A';
        commonActionsEl.textContent = 'N/A';
        devicePatternEl.textContent = 'Unknown';
        return;
    }
    
    const profile = data.profile;
    const stats = data.statistics;
    
    // Update confidence
    const confidence = Math.round((profile.pattern_confidence || 0) * 100);
    profileConfidenceEl.textContent = `${confidence}%`;
    
    // Update normal hours
    const loginHours = profile.login_hours || [];
    if (loginHours.length > 0) {
        const hoursStr = loginHours.map(h => `${h}:00`).join(', ');
        normalHoursEl.textContent = hoursStr;
    } else {
        normalHoursEl.textContent = 'Not established';
    }
    
    // Update average session
    const avgSessionMin = Math.round(stats.avg_session_duration_minutes || 0);
    avgSessionEl.textContent = `${avgSessionMin} minutes`;
    
    // Update common actions
    const commonActions = profile.common_actions || [];
    if (commonActions.length > 0) {
        commonActionsEl.textContent = commonActions.slice(0, 3).join(', ');
    } else {
        commonActionsEl.textContent = 'No pattern yet';
    }
    
    // Update device pattern
    const devices = profile.device_pattern || ['Web Browser'];
    devicePatternEl.textContent = devices.join(', ');
    
    // Update chart
    updateBehaviorChart(profile);
}

function initializeCharts() {
    const ctx = document.getElementById('behaviorChart').getContext('2d');
    
    behaviorChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Normal Activity Pattern',
                data: Array(24).fill(0),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }, {
                label: 'Current Activity',
                data: Array(24).fill(0),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#cbd5e1'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            }
        }
    });
}

function updateBehaviorChart(profile) {
    if (!behaviorChart) return;
    
    const hourlyPattern = profile.hourly_pattern || {};
    const currentHour = new Date().getHours();
    
    // Update normal pattern
    const normalData = Array.from({length: 24}, (_, i) => {
        const hour = i.toString();
        return hourlyPattern[hour] || Math.random() * 10 + 5; // Default pattern
    });
    
    // Update current activity (spike at current hour)
    const currentData = Array(24).fill(0);
    currentData[currentHour] = 50; // Simulate current activity
    
    behaviorChart.data.datasets[0].data = normalData;
    behaviorChart.data.datasets[1].data = currentData;
    behaviorChart.update();
}

async function loadSecurityAlerts() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/security/alerts`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateAlertsList(data.alerts || []);
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function updateAlertsList(alerts) {
    const activeAlerts = alerts.filter(alert => alert.status === 'active');
    const recentAlerts = alerts.slice(0, 5); // Show last 5 alerts
    
    // Update alert badge
    alertBadge.textContent = activeAlerts.length;
    
    // Update alerts list
    if (recentAlerts.length === 0) {
        alertsList.innerHTML = `
            <div class="no-alerts">
                <i class="fas fa-check-circle"></i>
                <p>No security alerts at this time</p>
            </div>
        `;
        return;
    }
    
    let alertsHTML = '';
    recentAlerts.forEach(alert => {
        const time = new Date(alert.created_at).toLocaleTimeString();
        const severityClass = alert.severity.toLowerCase();
        
        alertsHTML += `
            <div class="alert-item ${severityClass}">
                <div class="alert-header-small">
                    <span class="alert-title">${alert.alert_type}</span>
                    <span class="alert-time">${time}</span>
                </div>
                <p class="alert-message">${alert.description}</p>
                <div class="alert-score">Score: ${(alert.anomaly_score || 0).toFixed(2)} | Severity: ${alert.severity}</div>
            </div>
        `;
    });
    
    alertsList.innerHTML = alertsHTML;
}

async function performUserAction(actionType) {
    if (!authToken) return;
    
    actionCount++;
    actionCountEl.textContent = actionCount;
    
    // Map action types to resources
    const resources = {
        'view': 'document.pdf',
        'download': 'data_export.zip',
        'edit': 'report.docx',
        'delete': 'temp_file.txt'
    };
    
    const actionData = {
        action_type: actionType,
        resource: resources[actionType] || 'unknown',
        details: {
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent
        }
    };
    
    // Add to recent actions
    const actionTime = new Date().toLocaleTimeString();
    const actionItem = {
        type: actionType,
        time: actionTime,
        resource: actionData.resource
    };
    
    recentActions.unshift(actionItem);
    if (recentActions.length > 5) recentActions.pop();
    
    updateRecentActionsList();
    
    try {
        const response = await fetch(`${API_BASE_URL}/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(actionData)
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Check if anomaly was detected
            if (data.anomaly_detected) {
                if (data.force_logout) {
                    showForceLogoutModal(data.anomaly_score);
                } else {
                    showAlertModal(data.anomaly_score);
                }
            }
            
            // Update dashboard with new data
            loadDashboardData();
            
            // Show confirmation
            showNotification(`${actionType.charAt(0).toUpperCase() + actionType.slice(1)} action performed`, 'success');
        }
    } catch (error) {
        console.error('Error performing action:', error);
        showNotification('Failed to perform action', 'error');
    }
}

function updateRecentActionsList() {
    let actionsHTML = '';
    
    recentActions.forEach(action => {
        actionsHTML += `
            <div class="action-item ${action.type}">
                <div class="action-info">
                    <i class="fas fa-${getActionIcon(action.type)}"></i>
                    <span>${action.type.toUpperCase()}</span>
                </div>
                <div class="action-details">
                    <span class="action-resource">${action.resource}</span>
                    <span class="action-time">${action.time}</span>
                </div>
            </div>
        `;
    });
    
    recentActionsList.innerHTML = actionsHTML || '<p class="no-actions">No recent actions</p>';
}

function getActionIcon(actionType) {
    const icons = {
        'view': 'eye',
        'download': 'download',
        'edit': 'edit',
        'delete': 'trash'
    };
    return icons[actionType] || 'question-circle';
}

async function checkForAnomalies() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Check for high risk
            if (data.risk_level === 'HIGH' || data.anomaly_score > 0.9) {
                showAlertModal(data.anomaly_score, true);
            }
            
            // Update display
            updateDashboardStats(data);
        }
    } catch (error) {
        console.error('Error checking anomalies:', error);
    }
}

function showAlertModal(score, isAuto = false) {
    const alertTitle = document.getElementById('alertTitle');
    const alertMessage = document.getElementById('alertMessage');
    const alertScore = document.getElementById('alertScore');
    const alertAction = document.getElementById('alertAction');
    
    let title, message, action;
    
    if (score > 0.9) {
        title = 'CRITICAL ANOMALY DETECTED';
        message = 'High-risk behavior pattern detected. This may indicate a security threat.';
        action = 'Immediate verification required. Session may be terminated.';
    } else if (score > 0.7) {
        title = 'SUSPICIOUS ACTIVITY DETECTED';
        message = 'Unusual behavior pattern detected. Please verify your recent actions.';
        action = 'Review recent activities and confirm they are legitimate.';
    } else {
        title = 'UNUSUAL BEHAVIOR DETECTED';
        message = 'Minor deviations from normal behavior pattern detected.';
        action = 'Continue monitoring. No immediate action required.';
    }
    
    if (isAuto) {
        title = 'AUTO-DETECTED: ' + title;
    }
    
    alertTitle.textContent = title;
    alertMessage.textContent = message;
    alertScore.textContent = score.toFixed(2);
    alertAction.textContent = action;
    
    alertModal.style.display = 'flex';
}

function showForceLogoutModal(score) {
    forceLogoutModal.style.display = 'flex';
}

async function simulateAttack(attackType) {
    if (!authToken) return;
    
    showNotification(`Simulating ${attackType.replace('_', ' ')}...`, 'info');
    
    // Simulate multiple actions based on attack type
    const actions = {
        'insider_threat': [
            { type: 'login', delay: 0 },
            { type: 'view', delay: 1000 },
            { type: 'download', delay: 2000, repeat: 10 },
            { type: 'view', delay: 3000 },
            { type: 'download', delay: 4000, repeat: 5 }
        ],
        'credential_stuffing': [
            { type: 'login', delay: 0, repeat: 15 }
        ],
        'data_exfiltration': [
            { type: 'view', delay: 0, repeat: 20 },
            { type: 'download', delay: 100, repeat: 10 },
            { type: 'view', delay: 200, repeat: 10 }
        ]
    };
    
    const attackActions = actions[attackType] || [];
    
    // Show results panel
    const resultsPanel = document.getElementById('simulationResults');
    const resultsContent = document.getElementById('resultsContent');
    
    resultsContent.innerHTML = `
        <div class="simulation-in-progress">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Running ${attackType.replace('_', ' ')} simulation...</p>
        </div>
    `;
    
    resultsPanel.style.display = 'block';
    
    // Execute simulated actions
    let executedCount = 0;
    const totalActions = attackActions.reduce((sum, action) => sum + (action.repeat || 1), 0);
    
    for (const action of attackActions) {
        const repeat = action.repeat || 1;
        
        for (let i = 0; i < repeat; i++) {
            setTimeout(() => {
                // Simulate the action
                executedCount++;
                
                // Update progress
                if (executedCount >= totalActions) {
                    // Show final results
                    setTimeout(() => {
                        showSimulationResults(attackType);
                    }, 1000);
                }
            }, action.delay + (i * 500));
        }
    }
}

function showSimulationResults(attackType) {
    const resultsContent = document.getElementById('resultsContent');
    
    const simulations = {
        'insider_threat': {
            score: 0.85,
            alerts: 2,
            description: 'Simulated employee accessing sensitive data at unusual hours (2 AM).'
        },
        'credential_stuffing': {
            score: 0.95,
            alerts: 3,
            description: 'Simulated 15 rapid login attempts within 30 seconds.'
        },
        'data_exfiltration': {
            score: 0.78,
            alerts: 1,
            description: 'Simulated mass download of 30 files in quick succession.'
        }
    };
    
    const sim = simulations[attackType] || { score: 0.5, alerts: 0, description: 'Unknown simulation type' };
    
    resultsContent.innerHTML = `
        <div class="simulation-result ${sim.score > 0.8 ? 'high-risk' : sim.score > 0.6 ? 'medium-risk' : 'low-risk'}">
            <h4><i class="fas fa-${sim.score > 0.8 ? 'exclamation-triangle' : 'info-circle'}"></i> Simulation Complete</h4>
            <p>${sim.description}</p>
            
            <div class="result-stats">
                <div class="result-stat">
                    <span class="stat-label">Anomaly Score:</span>
                    <span class="stat-value ${sim.score > 0.8 ? 'text-danger' : sim.score > 0.6 ? 'text-warning' : 'text-success'}">${sim.score.toFixed(2)}</span>
                </div>
                <div class="result-stat">
                    <span class="stat-label">Alerts Triggered:</span>
                    <span class="stat-value">${sim.alerts}</span>
                </div>
                <div class="result-stat">
                    <span class="stat-label">Risk Level:</span>
                    <span class="stat-value ${sim.score > 0.8 ? 'text-danger' : sim.score > 0.6 ? 'text-warning' : 'text-success'}">
                        ${sim.score > 0.8 ? 'HIGH' : sim.score > 0.6 ? 'MEDIUM' : 'LOW'}
                    </span>
                </div>
            </div>
            
            <div class="result-message">
                <p><strong>System Response:</strong> ${sim.score > 0.8 ? 'Immediate alerts triggered, session monitoring enhanced' : 'Alerts logged for review'}</p>
            </div>
            
            <button class="btn-primary" onclick="loadDashboardData()">
                <i class="fas fa-sync-alt"></i> Refresh Dashboard
            </button>
        </div>
    `;
    
    // Update dashboard to show simulated effects
    setTimeout(() => {
        loadDashboardData();
        loadSecurityAlerts();
    }, 500);
}

function updateDashboard() {
    loadDashboardData();
    loadUserBehavior();
    loadSecurityAlerts();
}

function refreshDashboardData() {
    showNotification('Refreshing dashboard data...', 'info');
    updateDashboard();
}

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 
                 type === 'warning' ? 'exclamation-triangle' : 'info-circle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
        <button class="notification-close">&times;</button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : 
                    type === 'error' ? '#ef4444' : 
                    type === 'warning' ? '#f59e0b' : '#3b82f6'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
    `;
    
    // Add close button listener
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
    
    document.body.appendChild(notification);
    
    // Add CSS animations
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
}

// Export functions for use in browser console (for debugging)
window.cybersecurity = {
    performUserAction,
    simulateAttack,
    refreshDashboardData,
    showNotification,
    getCurrentUser: () => currentUser
};