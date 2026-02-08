/**
 * CrossInsure AI - Insurer Dashboard
 * Handles claim submission, image upload, and fraud analysis
 */

const API_BASE_URL = '/api';
const MAX_IMAGES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// State management
let selectedImages = [];
let isAnalyzing = false;
let currentCompany = 'Alpha Insurance';

// DOM Elements
const claimForm = document.getElementById('claimForm');
const uploadArea = document.getElementById('uploadArea');
const imageInput = document.getElementById('imageInput');
const imagePreviewContainer = document.getElementById('imagePreviewContainer');

const loadingContainer = document.getElementById('loadingContainer');
const errorContainer = document.getElementById('errorContainer');
const defaultContainer = document.getElementById('submitClaimView');

// ============================================================================
// FILE UPLOAD HANDLING
// ============================================================================

uploadArea.addEventListener('click', () => imageInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = Array.from(e.dataTransfer.files);
    handleImageFiles(files);
});

imageInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    
    // Check if total would exceed max
    if (files.length > MAX_IMAGES) {
        alert(`You can upload a maximum of ${MAX_IMAGES} images.`);
        imageInput.value = ''; // reset
        return;
    }
    
    handleImageFiles(files);
});

function handleImageFiles(files) {
    // Filter valid images
    let validFiles = files.filter(file => {
        // Check file type
        if (!file.type.startsWith('image/')) {
            showError(`${file.name} is not a valid image`);
            return false;
        }
        // Check file size
        if (file.size > MAX_FILE_SIZE) {
            showError(`${file.name} exceeds 10MB limit`);
            return false;
        }
        return true;
    });

    // Check total count
    if (selectedImages.length + validFiles.length > MAX_IMAGES) {
        showError(`Maximum ${MAX_IMAGES} images allowed. You have ${selectedImages.length} selected.`);
        return;
    }

    // Add files
    validFiles.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            selectedImages.push({
                file: file,
                dataUrl: e.target.result
            });
            renderImagePreview();
        };
        reader.readAsDataURL(file);
    });

    // Reset input
    imageInput.value = '';
}

function renderImagePreview() {
    imagePreviewContainer.innerHTML = '';
    selectedImages.forEach((image, index) => {
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="${image.dataUrl}" alt="Preview ${index + 1}">
            <div class="image-redaction-overlay">
                🔒 Masked before analysis
            </div>
            <button type="button" class="image-remove-btn" data-index="${index}">×</button>
        `;
        imagePreviewContainer.appendChild(preview);
    });

    // Attach remove handlers
    document.querySelectorAll('.image-remove-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const index = parseInt(btn.dataset.index);
            selectedImages.splice(index, 1);
            renderImagePreview();
        });
    });
}

// ============================================================================
// FORM SUBMISSION
// ============================================================================

claimForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validation
    if (selectedImages.length === 0) {
        showError('Please upload at least one image');
        return;
    }

    if (isAnalyzing) {
        return;
    }

    // Get location data
    const locationInputEl = document.getElementById('locationInput');
    const locationInput = locationInputEl ? locationInputEl.value.trim() : '';
    if (!locationInput) {
        showError('Please enter or select a location');
        return;
    }

    // Convert location to zone (using hash-based zoning)
    const locationZone = convertLocationToZone(locationInput);

    // Get date and times
    const incidentDateEl = document.getElementById('incidentDate');
    const incidentDate = incidentDateEl ? incidentDateEl.value : '';
    if (!incidentDate) {
        showError('Please select an incident date');
        return;
    }
    const timeStart = document.getElementById('incidentTimeStart').value || '00:00';
    const timeEnd = document.getElementById('incidentTimeEnd').value || '23:59';

    // Convert to ISO datetime format
    const dateTimeStart = `${incidentDate}T${timeStart}:00Z`;
    const dateTimeEnd = `${incidentDate}T${timeEnd}:00Z`;
    const dateTimeApprox = `${incidentDate}T12:00:00Z`;

    // Collect form data
    const formData = new FormData();
    formData.append('incident_type', document.getElementById('incidentType').value);
    formData.append('location_zone', locationZone);
    formData.append('damage_description', document.getElementById('incidentDescription').value);
    formData.append('incident_date_approx', dateTimeApprox);
    formData.append('incident_time_window_start', dateTimeStart);
    formData.append('incident_time_window_end', dateTimeEnd);

    // Add images
    selectedImages.forEach((image, index) => {
        formData.append('damage_images', image.file);
    });

    // Add Bearer token (default test token)
    let token = getAuthToken();
    if (!token) {
        const loggedIn = await autoLoginForCompany({ showToast: false });
        token = getAuthToken();
        if (!loggedIn || !token) {
            showError('Auto-login failed. Please refresh and try again.');
            return;
        }
    }

    isAnalyzing = true;
    showLoading();

    try {
        const sendAnalyzeRequest = async (authToken) => {
            return fetch(`${API_BASE_URL}/claims/analyze`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                },
                body: formData
            });
        };

        let response = await sendAnalyzeRequest(token);

        if (response.status === 401) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_company');
            const relogged = await autoLoginForCompany({ force: true, showToast: false });
            const newToken = getAuthToken();
            if (relogged && newToken) {
                response = await sendAnalyzeRequest(newToken);
            }
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
            
            // Extract meaningful error message
            let errorMsg = '';
            if (errorData.detail) {
                // FastAPI validation errors
                if (Array.isArray(errorData.detail)) {
                    errorMsg = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
                } else if (typeof errorData.detail === 'string') {
                    errorMsg = errorData.detail;
                } else {
                    errorMsg = JSON.stringify(errorData.detail);
                }
            } else if (errorData.message) {
                errorMsg = errorData.message;
            } else {
                errorMsg = `API error: ${response.status}`;
            }
            
            throw new Error(errorMsg);
        }

        const result = await response.json();
        
        // Store results (sessionStorage can fail across file:// pages)
        const serialized = JSON.stringify(result);
        sessionStorage.setItem('analysisResults', serialized);
        localStorage.setItem('analysisResults', serialized);
        window.location.href = 'results.html';
    } catch (error) {
        console.error('Claim analysis error:', error);
        hideAllContainers();
        
        // Extract error message
        const errorMessage = error.message || (typeof error === 'string' ? error : 'Failed to analyze claim. Please check your connection and try again.');
        
        showErrorMessage(errorMessage);
        isAnalyzing = false;
    }
});

// ============================================================================
// API RESULTS REDIRECT
// ============================================================================
// Results are now displayed on a separate page (results.html)
// Data is passed via sessionStorage

// ============================================================================
// STATE MANAGEMENT & UI UPDATES
// ============================================================================

function showLoading() {
    // Show loading state before redirect
    if (loadingContainer) {
        hideAllContainers();
        loadingContainer.classList.remove('hidden');
    }
}

function showErrorMessage(message) {
    document.getElementById('errorMessage').textContent = message;
    hideAllContainers();
    errorContainer.classList.remove('hidden');
}

function hideAllContainers() {
    if (loadingContainer) loadingContainer.classList.add('hidden');
    if (errorContainer) errorContainer.classList.add('hidden');
}

function showError(message) {
    // Show as temporary alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.style.position = 'fixed';
    alert.style.top = 'var(--spacing-lg)';
    alert.style.right = 'var(--spacing-lg)';
    alert.style.zIndex = '999';
    alert.style.maxWidth = '400px';
    alert.innerHTML = `
        <div class="alert-icon">⚠️</div>
        <div class="alert-content">
            <div class="alert-title">Validation Error</div>
            <div class="alert-message">${escapeHtml(message)}</div>
        </div>
    `;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

// ============================================================================
// AUTHENTICATION - AUTO LOGIN PER COMPANY
// ============================================================================

async function autoLoginForCompany(options = {}) {
    const { force = false, showToast = true } = options;
    const company = getCurrentCompany();
    if (!company) {
        console.error('No company selected for demo login');
        return false;
    }

    const existingToken = getAuthToken();
    const existingCompany = localStorage.getItem('auth_company');
    if (!force && existingToken && existingCompany === company) {
        return true;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/demo-login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: company
            })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('auth_company', company);
            console.log(`✅ Demo login for ${company}`);
            if (showToast) {
                showSuccess(`Switched to ${company}`);
            }
            return true;
        }

        console.error('Demo login failed:', await response.text());
        return false;
    } catch (error) {
        console.error('Auto-login error:', error);
        return false;
    }
}

function getAuthToken() {
    return localStorage.getItem('auth_token');
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert-popup success';
    alert.innerHTML = `
        <div class="alert-icon">✅</div>
        <div class="alert-content">
            <div class="alert-title">Success</div>
            <div class="alert-message">${escapeHtml(message)}</div>
        </div>
    `;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
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

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Insurer Dashboard initialized');
    console.log('API Base URL:', API_BASE_URL);
    
    // Show default state
    defaultContainer.classList.remove('hidden');
    
    // Setup company switcher
    setupCompanySelection();
    setupPopoverClickOutside();
    loadSavedCompany();
    
    // Initialize form features
    generateClaimReferenceId();
    setupSeveritySelection();
    setupFileUploadIntegration();
    setupFormSubmissionHook();
    
    // Auto-login for current company
    autoLoginForCompany({ showToast: false });
});

// ============================================================================
// COMPANY SWITCHER FUNCTIONALITY
// ============================================================================

function loadSavedCompany() {
    const saved = localStorage.getItem('selectedInsuranceCompany');
    if (saved) {
        currentCompany = saved;
        updateCompanyUI(saved);
    }
}

function updateCompanyUI(companyName) {
    currentCompany = companyName;
    const currentCompanyElement = document.getElementById('currentCompanyName');
    if (currentCompanyElement) {
        currentCompanyElement.textContent = companyName;
    }
    
    // Update active state in list
    document.querySelectorAll('.company-item').forEach(item => {
        const itemCompany = item.getAttribute('data-company');
        if (itemCompany === companyName) {
            item.classList.add('active');
            const badge = item.querySelector('.company-badge');
            if (!badge) {
                const badgeEl = document.createElement('span');
                badgeEl.className = 'company-badge';
                badgeEl.textContent = 'Active';
                item.appendChild(badgeEl);
            }
        } else {
            item.classList.remove('active');
            const badge = item.querySelector('.company-badge');
            if (badge) badge.remove();
        }
    });
}

function toggleCompanyPopover() {
    const popover = document.getElementById('companyPopover');
    if (popover) {
        if (popover.classList.contains('hidden')) {
            popover.classList.remove('hidden');
            popover.classList.add('animate-slide-down');
        } else {
            popover.classList.add('hidden');
            popover.classList.remove('animate-slide-down');
        }
    }
}

function setupPopoverClickOutside() {
    document.addEventListener('click', (e) => {
        const popover = document.getElementById('companyPopover');
        const btn = document.getElementById('companySwitcherBtn');
        
        if (popover && btn && !popover.contains(e.target) && !btn.contains(e.target)) {
            popover.classList.add('hidden');
        }
    });
}

function setupCompanySelection() {
    const companySwitcherBtn = document.getElementById('companySwitcherBtn');
    const companyItems = document.querySelectorAll('.company-item');

    if (companySwitcherBtn) {
        companySwitcherBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleCompanyPopover();
        });
    }

    companyItems.forEach(item => {
        item.addEventListener('click', async (e) => {
            e.stopPropagation();
            const companyName = item.getAttribute('data-company');
            
            // Save to localStorage
            localStorage.setItem('selectedInsuranceCompany', companyName);
            
            // Update UI
            updateCompanyUI(companyName);
            
            // Close popover
            const popover = document.getElementById('companyPopover');
            if (popover) {
                popover.classList.add('hidden');
            }
            
            // Auto-login to new company account
            await autoLoginForCompany({ force: true, showToast: true });
            
            console.log(`Switched to: ${companyName}`);
        });
    });
}

/**
 * Convert location to anonymized zone (zone_a through zone_e)
 * Uses simple hash-based distribution for privacy
 */
function convertLocationToZone(locationString) {
    if (!locationString) return 'zone_a';
    
    // Simple hash function to consistently map locations to zones
    let hash = 0;
    for (let i = 0; i < locationString.length; i++) {
        const char = locationString.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    
    // Map hash to one of 5 zones
    const zones = ['zone_a', 'zone_b', 'zone_c', 'zone_d', 'zone_e'];
    const index = Math.abs(hash) % zones.length;
    return zones[index];
}

function getCurrentCompany() {
    return currentCompany;
}

// ============================================================================
// MATCHED COMPANIES DISPLAY
// ============================================================================
// Now handled in results.js on the results page

// ============================================================================
// CLAIM REFERENCE ID GENERATION
// ============================================================================

function generateClaimReferenceId() {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    const refId = `CLM-${timestamp}-${random}`;
    const refIdElement = document.getElementById('claimReferenceId');
    if (refIdElement) {
        refIdElement.value = refId;
    }
}

// ============================================================================
// SEVERITY SELECTION
// ============================================================================

function setupSeveritySelection() {
    const severityOptions = document.querySelectorAll('.severity-option');
    const severityInputs = document.querySelectorAll('input[name="damageSeverity"]');
    
    // Add click handlers to severity option divs for direct interaction
    severityOptions.forEach((option, index) => {
        option.addEventListener('click', (e) => {
            e.stopPropagation();
            severityInputs[index].checked = true;
            severityInputs[index].dispatchEvent(new Event('change', { bubbles: true }));
        });
    });
    
    severityInputs.forEach((input, index) => {
        input.addEventListener('change', () => {
            // Reset all options
            severityOptions.forEach(opt => {
                opt.style.borderColor = '#E2E8F0';
                opt.style.backgroundColor = 'white';
                opt.classList.remove('active', 'ai-glow');
            });
            
            // Highlight selected option with AI glow
            if (input.checked) {
                const option = severityOptions[index];
                const severity = input.value;
                option.classList.add('active');
                
                if (severity === 'minor') {
                    option.style.borderColor = '#16A34A';
                    option.style.backgroundColor = '#d1fae5';
                } else if (severity === 'moderate') {
                    option.style.borderColor = '#F59E0B';
                    option.style.backgroundColor = '#fef3c7';
                    option.classList.add('ai-glow');
                } else if (severity === 'severe') {
                    option.style.borderColor = '#f97316';
                    option.style.backgroundColor = '#ffedd5';
                    option.classList.add('ai-glow');
                } else if (severity === 'critical') {
                    option.style.borderColor = '#DC2626';
                    option.style.backgroundColor = '#fee2e2';
                    option.classList.add('ai-glow');
                }
            }
        });
    });
}

// ============================================================================
// FILE UPLOAD INTEGRATION (Legacy Support)
// ============================================================================

function setupFileUploadIntegration() {
    // This integrates with the existing file upload system
    // The main file upload is already handled above in FILE UPLOAD HANDLING section
}

// ============================================================================
// FORM SUBMISSION HOOK
// ============================================================================

function setupFormSubmissionHook() {
    // Hook into form submission to set company field
    if (claimForm) {
        claimForm.addEventListener('submit', (e) => {
            // Set the current company in hidden field before submission
            const companyField = document.getElementById('selectedCompany');
            if (companyField) {
                companyField.value = getCurrentCompany();
            }
            console.log('Submitting claim for:', getCurrentCompany());
        });
    }
}
