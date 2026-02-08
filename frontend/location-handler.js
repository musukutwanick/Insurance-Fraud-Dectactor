/* ============================================================================
   LOCATION AUTOCOMPLETE & MAP SELECTION HANDLER
============================================================================ */

let map = null;
let selectedMarker = null;
let selectedLocationData = {
    name: '',
    latitude: null,
    longitude: null
};

// Initialize location input with autocomplete
document.addEventListener('DOMContentLoaded', function() {
    const locationInput = document.getElementById('locationInput');
    const mapSelectBtn = document.getElementById('mapSelectBtn');
    const mapModal = document.getElementById('mapModal');
    const closeMapBtn = document.getElementById('closeMapBtn');
    const cancelMapBtn = document.getElementById('cancelMapBtn');
    const confirmLocationBtn = document.getElementById('confirmLocationBtn');

    if (!locationInput) return;

    // Location input autocomplete
    locationInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        const suggestionsDiv = document.getElementById('locationSuggestions');

        if (query.length < 2) {
            suggestionsDiv.classList.add('hidden');
            return;
        }

        fetchLocationSuggestions(query, suggestionsDiv);
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('[id="locationInput"]') && !e.target.closest('[id="locationSuggestions"]')) {
            document.getElementById('locationSuggestions').classList.add('hidden');
        }
    });

    // Map selection button
    if (mapSelectBtn) {
        mapSelectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openMapModal();
        });
    }

    // Modal close buttons
    if (closeMapBtn) {
        closeMapBtn.addEventListener('click', () => closeModal());
    }
    if (cancelMapBtn) {
        cancelMapBtn.addEventListener('click', () => closeModal());
    }

    // Confirm location from map
    if (confirmLocationBtn) {
        confirmLocationBtn.addEventListener('click', function() {
            if (selectedLocationData.latitude && selectedLocationData.longitude) {
                const locationInput = document.getElementById('locationInput');
                locationInput.value = selectedLocationData.name || selectedLocationData.fullAddress || 
                                     `${selectedLocationData.latitude.toFixed(4)}, ${selectedLocationData.longitude.toFixed(4)}`;
                updateLocationDisplay();
                closeModal();
                
                // Remove required attribute since location is now selected
                locationInput.removeAttribute('required');
            } else {
                alert('Please click on the map to select a location');
            }
        });
    }

    // Close modal when clicking outside
    if (mapModal) {
        mapModal.addEventListener('click', function(e) {
            if (e.target === mapModal) {
                closeModal();
            }
        });
    }
});

/**
 * Fetch location suggestions from Nominatim (OpenStreetMap)
 */
async function fetchLocationSuggestions(query, suggestionsDiv) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?` +
            `q=${encodeURIComponent(query)}&format=json&limit=8`
        );
        const results = await response.json();

        suggestionsDiv.innerHTML = '';

        if (results.length === 0) {
            suggestionsDiv.innerHTML = `
                <div style="padding: 1rem; text-align: center; color: #6B7280;">
                    No locations found
                </div>
            `;
            suggestionsDiv.classList.remove('hidden');
            return;
        }

        results.forEach(location => {
            const item = document.createElement('div');
            item.className = 'location-suggestion-item';
            item.innerHTML = `
                <i class="fa-solid fa-location-dot"></i>
                <div>
                    <strong>${location.name || location.display_name.split(',')[0]}</strong>
                    <div style="font-size: 0.8rem; color: #6B7280;">${location.display_name.substring(0, 60)}...</div>
                </div>
            `;

            item.addEventListener('click', function() {
                selectLocation(
                    location.name || location.display_name.split(',')[0],
                    location.display_name,
                    parseFloat(location.lat),
                    parseFloat(location.lon)
                );
            });

            suggestionsDiv.appendChild(item);
        });

        suggestionsDiv.classList.remove('hidden');
    } catch (error) {
        console.error('Error fetching locations:', error);
        suggestionsDiv.innerHTML = `
            <div style="padding: 1rem; text-align: center; color: #DC2626;">
                Error loading suggestions
            </div>
        `;
        suggestionsDiv.classList.remove('hidden');
    }
}

/**
 * Select a location from autocomplete
 */
function selectLocation(name, fullAddress, latitude, longitude) {
    selectedLocationData = {
        name: name,
        fullAddress: fullAddress,
        latitude: latitude,
        longitude: longitude
    };

    const locationInput = document.getElementById('locationInput');
    locationInput.value = name;
    locationInput.removeAttribute('required'); // Location is now selected
    document.getElementById('locationSuggestions').classList.add('hidden');
    updateLocationDisplay();
}

/**
 * Update the location display text
 */
function updateLocationDisplay() {
    const displayDiv = document.getElementById('selectedLocationDisplay');
    if (selectedLocationData.latitude) {
        displayDiv.innerHTML = `
            <i class="fa-solid fa-check" style="color: #16A34A; margin-right: 0.5rem;"></i>
            <strong>${selectedLocationData.name}</strong>
            <br>
            <small style="color: #6B7280;">Lat: ${selectedLocationData.latitude.toFixed(4)}, 
            Lon: ${selectedLocationData.longitude.toFixed(4)}</small>
        `;
    }
}

/**
 * Open map modal for location selection
 */
function openMapModal() {
    const mapModal = document.getElementById('mapModal');
    mapModal.classList.remove('hidden');

    // Initialize map after a short delay to ensure container is visible
    setTimeout(() => {
        if (!map) {
            initializeMap();
        }
    }, 100);
}

/**
 * Close map modal
 */
function closeModal() {
    document.getElementById('mapModal').classList.add('hidden');
}

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    const mapContainer = document.getElementById('map');

    // Default to a central location (e.g., United States center)
    let defaultLat = 39.8283;
    let defaultLon = -98.5795;
    let defaultZoom = 4;

    // If location is already selected, center on it
    if (selectedLocationData.latitude) {
        defaultLat = selectedLocationData.latitude;
        defaultLon = selectedLocationData.longitude;
        defaultZoom = 13;
    }

    // Destroy existing map if it exists
    if (map) {
        map.remove();
        map = null;
    }

    // Create new map
    map = L.map('map').setView([defaultLat, defaultLon], defaultZoom);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Add existing marker if location is selected
    if (selectedLocationData.latitude) {
        addMapMarker(selectedLocationData.latitude, selectedLocationData.longitude);
    }

    // Handle map clicks
    map.on('click', function(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        addMapMarker(lat, lng);
        reverseGeocode(lat, lng);
    });
}

/**
 * Add marker to map
 */
function addMapMarker(lat, lng) {
    // Remove existing marker
    if (selectedMarker) {
        map.removeLayer(selectedMarker);
    }

    // Add new marker
    selectedMarker = L.marker([lat, lng], {
        icon: L.icon({
            iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            shadowSize: [41, 41],
            shadowAnchor: [12, 41]
        })
    }).addTo(map);

    selectedLocationData.latitude = lat;
    selectedLocationData.longitude = lng;

    // Center map on marker
    map.setView([lat, lng], map.getZoom());
}

/**
 * Reverse geocode coordinates to get location name
 */
async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`
        );
        const data = await response.json();

        const locationName = data.address?.city || 
                            data.address?.town || 
                            data.address?.county || 
                            data.address?.state ||
                            `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

        selectedLocationData.name = locationName;
        selectedLocationData.fullAddress = data.display_name;

        // Update marker popup
        if (selectedMarker) {
            selectedMarker.bindPopup(`
                <strong>${locationName}</strong><br>
                Lat: ${lat.toFixed(4)}<br>
                Lon: ${lng.toFixed(4)}
            `).openPopup();
        }
    } catch (error) {
        console.error('Error reverse geocoding:', error);
        selectedLocationData.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }
}
