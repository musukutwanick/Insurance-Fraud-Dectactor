/**
 * CrossInsure AI - Results Page
 * Displays fraud analysis results with modern UI
 */

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Results page initialized');
    
    // Check if we have results data
    const resultsData = sessionStorage.getItem('analysisResults') || localStorage.getItem('analysisResults');
    
    if (!resultsData) {
        // No results data - redirect back to form
        console.error('No analysis results found');
        setTimeout(() => {
            window.location.href = 'insurer.html';
        }, 2000);
        return;
    }
    
    // Parse and display results
    try {
        const data = JSON.parse(resultsData);
        sessionStorage.removeItem('analysisResults');
        localStorage.removeItem('analysisResults');
        displayResults(data);
    } catch (error) {
        console.error('Error parsing results:', error);
        showError('Failed to load results data');
    }
});

// ============================================================================
// RESULTS DISPLAY
// ============================================================================

function displayResults(data) {
    console.log('Displaying results:', data);
    
    // Update reference ID and  processing time
    document.getElementById('referenceId').textContent = data.claim_reference_id || 'N/A';
    document.getElementById('processingTime').textContent = data.processing_time_ms ? `${data.processing_time_ms}ms` : 'N/A';

    // Update risk circle
    const riskCircle = document.getElementById('riskCircle');
    const riskScore = document.getElementById('riskScore');
    const riskLabel = document.getElementById('riskLabel');

    const riskClass = getRiskClass(data.fraud_risk_level);
    riskCircle.className = `risk-circle ${riskClass}`;
    riskScore.textContent = Math.round(data.fraud_risk_score * 100) + '%';
    riskLabel.textContent = formatRiskLevel(data.fraud_risk_level);

    // Update recommendation banner
    const banner = document.getElementById('recommendationBanner');
    const recommendationClass = data.recommendation ? data.recommendation.toLowerCase() : 'proceed';
    banner.className = `recommendation-banner ${recommendationClass}`;
    
    const iconMap = {
        'proceed': 'fa-check-circle',
        'hold': 'fa-pause-circle',
        'investigate': 'fa-exclamation-circle'
    };
    const icon = iconMap[recommendationClass] || 'fa-info-circle';
    banner.innerHTML = `<i class="fas ${icon}"></i> ${formatRecommendation(data.recommendation)}`;

    // Update matched incidents count
    document.getElementById('matchedCount').textContent = data.matched_incidents_count || 0;

    // Display matched companies if available
    if (data.matched_companies && data.matched_companies.length > 0) {
        displayMatchedCompanies(data.matched_companies);
    } else {
        document.getElementById('matchedCompaniesContainer').style.display = 'none';
    }

    // Update risk factors
    const factorsList = document.getElementById('riskFactorsList');
    if (data.risk_factors && data.risk_factors.length > 0) {
        factorsList.innerHTML = data.risk_factors
            .map(factor => `<li><i class="fas fa-exclamation-triangle"></i> ${escapeHtml(factor)}</li>`)
            .join('');
    } else {
        factorsList.innerHTML = '<li class="no-risk"><i class="fas fa-check-circle"></i> No significant risk factors identified</li>';
    }

    // Update explanation
    document.getElementById('explanationText').textContent = data.explanation || 'No detailed analysis available.';

    // Hide loading, show results
    document.getElementById('loadingContainer').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'grid';
}

function getRiskClass(level) {
    const levelMap = {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'CRITICAL': 'high'
    };
    return levelMap[level] || 'low';
}

function formatRiskLevel(level) {
    const levelMap = {
        'LOW': 'Low Risk',
        'MEDIUM': 'Medium Risk',
        'HIGH': 'High Risk',
        'CRITICAL': 'Critical Risk'
    };
    return levelMap[level] || level;
}

function formatRecommendation(recommendation) {
    const recMap = {
        'PROCEED': 'PROCEED WITH CLAIM',
        'HOLD': 'HOLD FOR REVIEW',
        'INVESTIGATE': 'INVESTIGATE IMMEDIATELY'
    };
    return recMap[recommendation] || recommendation;
}

// ============================================================================
// MATCHED COMPANIES DISPLAY
// ============================================================================

function displayMatchedCompanies(companies) {
    const container = document.getElementById('matchedCompaniesList');
    const matchedSection = document.getElementById('matchedCompaniesContainer');
    const currentCompany = localStorage.getItem('selectedInsuranceCompany') || 'Alpha Insurance';
    
    if (!container || !matchedSection) return;
    
    if (!companies || companies.length === 0) {
        matchedSection.style.display = 'none';
        return;
    }
    
    matchedSection.style.display = 'block';
    container.innerHTML = '';
    
    companies.forEach(company => {
        const badge = document.createElement('div');
        const isCurrent = company === currentCompany;
        badge.className = isCurrent ? 'company-badge-modern current' : 'company-badge-modern';
        badge.innerHTML = `
            <i class="fas fa-building"></i>
            ${escapeHtml(company)}
            ${isCurrent ? ' <i class="fas fa-star"></i>' : ''}
        `;
        container.appendChild(badge);
    });
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('loadingContainer').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'none';
    document.getElementById('errorContainer').style.display = 'block';
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
