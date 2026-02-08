/**
 * CrossInsure AI - Admin Dashboard
 * Handles metrics fetching, system health monitoring, and chart rendering
 */

const API_BASE_URL = '/api';
const REFRESH_INTERVAL = 30000; // 30 seconds

// Chart instances
let riskDistributionChart = null;
let incidentTypeChart = null;

// Auto-refresh timer
let refreshTimer = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Admin Dashboard initialized');
    console.log('API Base URL:', API_BASE_URL);
    
    // Initial data fetch
    loadAllData();
    
    // Refresh button handler
    document.getElementById('refreshBtn').addEventListener('click', loadAllData);
    
    // Auto-refresh every 30 seconds
    refreshTimer = setInterval(loadAllData, REFRESH_INTERVAL);
});

// ============================================================================
// DATA FETCHING
// ============================================================================

async function loadAllData() {
    const token = getAuthToken();
    if (!token) {
        console.warn('No authentication token available');
        return;
    }

    try {
        // Fetch both metrics and health in parallel
        const [metricsData, healthData] = await Promise.all([
            fetchMetrics(token),
            fetchSystemHealth(token)
        ]);

        if (metricsData) {
            displayMetrics(metricsData);
        }

        if (healthData) {
            displayHealth(healthData);
        }

        updateLastUpdated();
    } catch (error) {
        console.error('Data loading error:', error);
    }
}

async function fetchMetrics(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/metrics`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Metrics API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return null;
    }
}

async function fetchSystemHealth(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/system-health`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Health API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching system health:', error);
        return null;
    }
}

// ============================================================================
// METRICS DISPLAY
// ============================================================================

function displayMetrics(data) {
    // Total metrics
    document.getElementById('totalClaims').textContent = 
        formatNumber(data.total_claims_analyzed || 0);
    
    document.getElementById('totalFingerprints').textContent = 
        formatNumber(data.total_fingerprints_stored || 0);
    
    document.getElementById('claimsTodayCount').textContent = 
        formatNumber(data.claims_analyzed_today || 0);
    
    document.getElementById('fingerprintsTodayCount').textContent = 
        formatNumber(data.fingerprints_added_today || 0);

    // Risk breakdown
    const riskCounts = data.risk_breakdown || {};
    document.getElementById('highRiskCount').textContent = 
        formatNumber(riskCounts.high || 0);

    // Average fraud score
    const avgScore = (data.average_fraud_risk_score || 0) * 100;
    document.getElementById('avgFraudScore').textContent = 
        avgScore.toFixed(1) + '%';

    // Time period breakdown
    displayTimePeriodMetrics(data);

    // Update charts
    updateRiskDistributionChart(riskCounts);
    updateIncidentTypeChart(data.incident_types || {});
}

function displayTimePeriodMetrics(data) {
    // This Week
    const week = data.claims_analyzed_week || 0;
    document.getElementById('claimsThisWeek').textContent = formatNumber(week);
    document.getElementById('lowWeek').textContent = 
        formatNumber(data.risk_breakdown_week?.low || 0);
    document.getElementById('mediumWeek').textContent = 
        formatNumber(data.risk_breakdown_week?.medium || 0);
    document.getElementById('highWeek').textContent = 
        formatNumber(data.risk_breakdown_week?.high || 0);

    // This Month
    const month = data.claims_analyzed_month || 0;
    document.getElementById('claimsThisMonth').textContent = formatNumber(month);
    document.getElementById('lowMonth').textContent = 
        formatNumber(data.risk_breakdown_month?.low || 0);
    document.getElementById('mediumMonth').textContent = 
        formatNumber(data.risk_breakdown_month?.medium || 0);
    document.getElementById('highMonth').textContent = 
        formatNumber(data.risk_breakdown_month?.high || 0);

    // This Year
    const year = data.claims_analyzed_year || 0;
    document.getElementById('claimsThisYear').textContent = formatNumber(year);
    document.getElementById('lowYear').textContent = 
        formatNumber(data.risk_breakdown_year?.low || 0);
    document.getElementById('mediumYear').textContent = 
        formatNumber(data.risk_breakdown_year?.medium || 0);
    document.getElementById('highYear').textContent = 
        formatNumber(data.risk_breakdown_year?.high || 0);
}

// ============================================================================
// HEALTH DISPLAY
// ============================================================================

function displayHealth(data) {
    // Status
    const status = data.status || 'unknown';
    document.getElementById('systemStatus').textContent = 
        status === 'healthy' ? 'System Online' : 'System Issues Detected';

    // API Response Time
    document.getElementById('apiResponseTime').textContent = 
        Math.round(data.api_response_time_ms || 0);

    // Database Status
    const dbConnected = data.database_connected || false;
    document.getElementById('databaseStatus').innerHTML = 
        dbConnected ? '✓ Connected' : '✗ Disconnected';
    document.getElementById('databaseStatus').style.color = 
        dbConnected ? 'var(--color-risk-low)' : 'var(--color-risk-high)';

    // Update status indicator color
    const healthStatus = document.getElementById('healthStatus');
    if (status === 'healthy') {
        healthStatus.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
        healthStatus.style.borderColor = 'rgba(16, 185, 129, 0.3)';
    } else {
        healthStatus.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        healthStatus.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }
}

// ============================================================================
// CHART RENDERING (Canvas-based)
// ============================================================================

function updateRiskDistributionChart(riskCounts) {
    const canvas = document.getElementById('riskDistributionChart');
    const ctx = canvas.getContext('2d');

    // Clear previous chart
    if (riskDistributionChart) {
        riskDistributionChart.destroy();
    }

    // Prepare data
    const low = riskCounts.low || 0;
    const medium = riskCounts.medium || 0;
    const high = riskCounts.high || 0;
    const critical = riskCounts.critical || 0;
    const total = low + medium + high + critical || 1;

    // Create simple bar chart with canvas
    drawBarChart(
        ctx,
        ['Low Risk', 'Medium Risk', 'High Risk', 'Critical'],
        [low, medium, high, critical],
        ['#10B981', '#F59E0B', '#EF4444', '#7C3AED'],
        'Risk Level Distribution'
    );
}

function updateIncidentTypeChart(incidentTypes) {
    const canvas = document.getElementById('incidentTypeChart');
    const ctx = canvas.getContext('2d');

    // Clear previous chart
    if (incidentTypeChart) {
        incidentTypeChart.destroy();
    }

    // Prepare data
    const labels = Object.keys(incidentTypes);
    const values = Object.values(incidentTypes);

    if (labels.length === 0) {
        // Show placeholder
        ctx.font = '14px sans-serif';
        ctx.fillStyle = '#D1D5DB';
        ctx.textAlign = 'center';
        ctx.fillText('No incident data available yet', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Create pie chart
    drawPieChart(
        ctx,
        labels.map(label => formatIncidentType(label)),
        values
    );
}

function drawBarChart(ctx, labels, values, colors, title) {
    const canvas = ctx.canvas;
    const padding = 40;
    const chartHeight = canvas.height - padding * 2;
    const chartWidth = canvas.width - padding * 2;
    const barWidth = chartWidth / (labels.length * 1.5);
    const maxValue = Math.max(...values, 1);

    // Background
    ctx.fillStyle = 'transparent';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Title
    ctx.font = '14px sans-serif';
    ctx.fillStyle = '#D1D5DB';
    ctx.textAlign = 'center';
    ctx.fillText(title, canvas.width / 2, 20);

    // Draw bars
    values.forEach((value, index) => {
        const barHeight = (value / maxValue) * chartHeight;
        const x = padding + index * (barWidth * 1.5) + (barWidth * 0.25);
        const y = canvas.height - padding - barHeight;

        // Bar
        ctx.fillStyle = colors[index];
        ctx.fillRect(x, y, barWidth, barHeight);

        // Value label
        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = '#F0F8FF';
        ctx.textAlign = 'center';
        ctx.fillText(
            value,
            x + barWidth / 2,
            y - 5
        );

        // Label
        ctx.font = '11px sans-serif';
        ctx.fillStyle = '#D1D5DB';
        ctx.textAlign = 'center';
        ctx.save();
        ctx.translate(x + barWidth / 2, canvas.height - padding + 20);
        ctx.rotate(-Math.PI / 4);
        ctx.fillText(labels[index], 0, 0);
        ctx.restore();
    });

    // Y-axis labels
    ctx.font = '10px sans-serif';
    ctx.fillStyle = '#D1D5DB';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
        const yValue = Math.round((maxValue * i) / 4);
        const y = canvas.height - padding - (chartHeight * i) / 4;
        ctx.fillText(yValue, padding - 10, y + 3);
    }
}

function drawPieChart(ctx, labels, values) {
    const canvas = ctx.canvas;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 60;

    const total = values.reduce((a, b) => a + b, 0);
    const colors = ['#10B981', '#F59E0B', '#EF4444', '#7C3AED', '#3B82F6'];

    let currentAngle = -Math.PI / 2;

    values.forEach((value, index) => {
        const sliceAngle = (value / total) * 2 * Math.PI;

        // Draw slice
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
        ctx.lineTo(centerX, centerY);
        ctx.fillStyle = colors[index % colors.length];
        ctx.fill();

        // Draw label
        const labelAngle = currentAngle + sliceAngle / 2;
        const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
        const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = '#FFFFFF';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const percentage = ((value / total) * 100).toFixed(1);
        ctx.fillText(`${percentage}%`, labelX, labelY);

        currentAngle += sliceAngle;
    });

    // Draw legend
    let legendY = canvas.height - 80;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'left';

    labels.forEach((label, index) => {
        // Color box
        ctx.fillStyle = colors[index % colors.length];
        ctx.fillRect(20, legendY, 12, 12);

        // Label
        ctx.fillStyle = '#D1D5DB';
        ctx.fillText(label, 40, legendY + 10);

        legendY += 20;
    });
}

// ============================================================================
// AUTHENTICATION
// ============================================================================

function getAuthToken() {
    // Try to get from localStorage
    let token = localStorage.getItem('auth_token');
    
    // If not found, prompt user
    if (!token) {
        token = prompt('Enter your authentication token (admin required):');
        if (token) {
            localStorage.setItem('auth_token', token);
        }
    }
    
    return token;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatIncidentType(type) {
    const typeMap = {
        'auto_collision': 'Auto Collision',
        'property_damage': 'Property Damage',
        'water_damage': 'Water Damage',
        'theft': 'Theft',
        'vandalism': 'Vandalism',
        'natural_disaster': 'Natural Disaster',
        'other': 'Other'
    };
    return typeMap[type] || type;
}

function updateLastUpdated() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    document.getElementById('lastUpdated').textContent = timeStr;
}

// ============================================================================
// CLEANUP
// ============================================================================

window.addEventListener('beforeunload', () => {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
});
