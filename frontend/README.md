# CrossInsure AI - Frontend Dashboard

Professional, privacy-first frontend for the CrossInsure AI insurance fraud detection system.

## 🎯 Overview

The frontend consists of two modern, enterprise-grade dashboards built with vanilla HTML5, CSS3, and JavaScript:

- **Insurer Dashboard** (`insurer.html`) - For claim submission and fraud analysis
- **Admin Dashboard** (`admin.html`) - For system monitoring and metrics

## 🎨 Design System

### Color Palette
- **Primary Background**: Black (#000000)
- **Card Background**: Alice Blue (#F0F8FF)
- **Accent Glow**: Alice Blue with soft transparency
- **Status Colors**:
  - Low Risk: #10B981 (Green)
  - Medium Risk: #F59E0B (Amber)
  - High Risk: #EF4444 (Red)
  - Critical Risk: #7C3AED (Purple)

### Design Features
- Rounded cards with soft shadows
- Smooth hover effects and transitions
- Loading spinners with animations
- Responsive grid layouts (mobile-friendly)
- Privacy-first visual messaging
- Enterprise-grade typography

## 📁 File Structure

```
frontend/
├── insurer.html          # Claim submission dashboard
├── admin.html            # System monitoring dashboard
├── styles.css            # Design system and component styles
├── insurer.js            # Insurer dashboard logic
├── admin.js              # Admin dashboard logic
└── README.md             # This file
```

## 🚀 Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Edge, Safari)
- FastAPI backend running on `http://localhost:8000`
- Valid authentication token from backend

### Running the Frontend

#### Option 1: Using a Simple HTTP Server (Recommended)

**Python 3.x:**
```bash
cd frontend
python -m http.server 8080
# Open browser: http://localhost:8080
```

**Node.js:**
```bash
cd frontend
npx http-server -p 8080
# Open browser: http://localhost:8080
```

#### Option 2: Direct File Access
Simply open `insurer.html` or `admin.html` in your browser using `file://` protocol.

**Note:** CORS requests require backend to be configured correctly (which it is by default).

## 🔐 Authentication

### Getting an Authorization Token

1. **Initialize the Backend Database:**
   ```bash
   python init_db.py
   ```
   This creates two test users:
   - **Admin User**: `username: admin` / `password: admin123`
   - **Insurer User**: `username: insurer1` / `password: insurer123`

2. **Login to Get Token:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "insurer1", "password": "insurer123"}'
   ```
   
   Response:
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "token_type": "bearer",
     "expires_in": 1800
   }
   ```

3. **Use Token in Frontend:**
   - The dashboard will prompt for a token on first load
   - Enter the `access_token` value
   - Token is stored in browser's `localStorage`
   - Clear it anytime by opening browser console: `localStorage.removeItem('auth_token')`

### Token Management

- **Access Token Lifetime**: 30 minutes
- **Refresh Token Lifetime**: 7 days
- **Storage**: Browser localStorage (cleared on logout)
- **Header Format**: `Authorization: Bearer <token>`

## 📊 Insurer Dashboard Features

### 1. Claim Submission Form
- **Incident Type Selection**: Auto Collision, Property Damage, Water Damage, Theft, Vandalism, Natural Disaster, Other
- **Location Zone**: Urban, Suburban, Rural
- **Damage Description**: Detailed text input
- **Date/Time Window**: Incident date and approximate time range
- **Image Upload**: 
  - Drag & drop or click to upload
  - Support for JPG/PNG up to 10MB each
  - Maximum 5 images per claim
  - Real-time preview with redaction indicator

### 2. Fraud Analysis Results
Displays immediate fraud risk assessment:
- **Risk Score Circle**: Visual 0-100% indicator (Low/Medium/High/Critical)
- **Recommendation**: Proceed/Hold/Investigate banner
- **Matched Incidents**: Count of similar cases in database
- **Risk Factors**: List of identified fraud indicators
- **Detailed Explanation**: AI-generated analysis summary
- **Processing Time**: Milliseconds to analyze

### 3. Privacy Features
- Sensitive data masking indicator
- Privacy-first design messaging
- Data protection confirmation on results
- No personal information exposed in analysis

## 🔧 Admin Dashboard Features

### 1. System Health Monitoring
- **Overall Status**: System operational status with pulse indicator
- **API Response Time**: Real-time performance metrics
- **Database Connection**: Status indicator
- **Component Status**: 6 service components (Auth, Image Processing, Embeddings, Fingerprinting, Fraud Scoring, Storage)

### 2. Key Metrics
- **Total Claims**: Lifetime claims analyzed
- **Fingerprints Stored**: Total incident fingerprints in database
- **High Risk Claims**: Count of flagged claims
- **Average Fraud Score**: System-wide average fraud risk

### 3. Time Period Breakdown
- **This Week**: Claims and risk distribution for current week
- **This Month**: Claims and risk distribution for current month
- **This Year**: Claims and risk distribution for calendar year
- Each shows Low/Medium/High risk breakdown

### 4. Charts & Visualizations
- **Risk Distribution Bar Chart**: Visual breakdown by risk level
- **Incident Type Pie Chart**: Claims distribution by incident category
- Canvas-based rendering (no external charting library)

### 5. Real-Time Updates
- **Auto-Refresh**: Metrics update every 30 seconds
- **Manual Refresh**: Click "Refresh Metrics" button
- **Last Updated**: Timestamp of most recent data fetch

## 🔌 API Integration

### Insurer Dashboard Endpoints

**Submit Claim for Analysis**
```
POST /api/claims/analyze
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Fields:
- incident_type: string (enum)
- damage_description: string
- location_zone: string (enum)
- incident_date_approx: date (YYYY-MM-DD)
- incident_time_window_start: time (HH:MM)
- incident_time_window_end: time (HH:MM)
- damage_images: file[] (up to 5 images)

Response: {
  "claim_reference_id": "CLM-2024-xxxxx",
  "fraud_risk_score": 0.65,
  "fraud_risk_level": "MEDIUM",
  "recommendation": "HOLD",
  "matched_incidents_count": 3,
  "top_match": { ... },
  "risk_factors": ["Factor 1", "Factor 2"],
  "explanation": "Analysis details...",
  "processing_time_ms": 245
}
```

### Admin Dashboard Endpoints

**Get System Metrics**
```
GET /api/admin/metrics
Authorization: Bearer <admin_token>

Response: {
  "total_claims_analyzed": 125,
  "total_fingerprints_stored": 128,
  "high_risk_count": 12,
  "medium_risk_count": 35,
  "low_risk_count": 78,
  "claims_analyzed_today": 5,
  "claims_analyzed_week": 42,
  "claims_analyzed_month": 128,
  "average_fraud_risk_score": 0.38,
  "fingerprints_added_today": 4,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Get System Health**
```
GET /api/admin/system-health
Authorization: Bearer <admin_token>

Response: {
  "status": "healthy",
  "database_connected": true,
  "api_response_time_ms": 45,
  "components": {
    "auth_service": "operational",
    "image_processing": "operational",
    "embeddings": "operational",
    "fingerprinting": "operational",
    "fraud_scoring": "operational",
    "storage": "operational"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔒 Privacy & Security

### Design Principles
1. **Data Minimization**: Only necessary incident fingerprints stored
2. **Anonymization**: Personal data masked before processing
3. **No Raw Media**: Images not persisted, only embeddings
4. **Transparent Processing**: Users informed about data handling
5. **Audit Trails**: All operations logged with timestamps

### Implementation
- Bearer token authentication (JWT)
- No sensitive data in API responses
- Client-side image processing validation
- HTTPS recommended for production
- CORS configured for backend security
- XSS protection via HTML escaping

## 🛠️ Development

### File Size
- `styles.css`: ~15 KB (1000+ lines)
- `insurer.html`: ~12 KB (400+ lines)
- `insurer.js`: ~10 KB (350+ lines)
- `admin.html`: ~10 KB (300+ lines)
- `admin.js`: ~12 KB (400+ lines)
- **Total**: ~59 KB (all minifiable)

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### No External Dependencies
- Pure HTML5, CSS3, ES6+ JavaScript
- Canvas API for charts
- Fetch API for HTTP requests
- No frameworks, libraries, or build tools required
- Single-page application pattern

## 🚨 Error Handling

### User Feedback
- **Alert Messages**: Toast-style alerts for validation errors
- **Loading States**: Spinner with status text during processing
- **Error Messages**: Clear error descriptions with remediation
- **Validation**: Client-side validation before submission

### Common Issues

**"No authentication token found"**
- Solution: Ensure backend is running and you have a valid token

**"API error: 401 Unauthorized"**
- Solution: Token expired (30 min lifetime). Generate a new one.

**"CORS policy blocked"**
- Solution: Ensure backend running on `localhost:8000` with CORS enabled

**"Failed to analyze claim"**
- Solution: Check backend logs, ensure images are valid JPG/PNG

## 📈 Performance

### Optimization
- Lazy image loading with preview
- Minimal CSS (single stylesheet)
- Efficient DOM manipulation
- No unnecessary re-renders
- Debounced API calls

### Metrics
- Page load: <1s (with backend)
- Image upload: Instant preview
- Claim analysis: Depends on backend (typically 200-500ms)
- Metrics refresh: <100ms (with network)

## 🔄 Workflows

### Claim Submission Flow
1. User fills claim form
2. Selects incident type, location, damage details
3. Uploads damage images (with preview)
4. Clicks "Analyze Claim"
5. Loading spinner shown during processing
6. Results displayed with risk assessment
7. User can submit new claim or view details

### Admin Monitoring Flow
1. Admin logs in with admin token
2. Dashboard loads system metrics and health
3. Metrics auto-refresh every 30 seconds
4. Charts update with new data
5. Click "Refresh Metrics" for immediate update
6. Monitor system health and performance
7. Review claim trends and risk distribution

## 📚 Integration Checklist

- [x] Insurer dashboard (claim submission)
- [x] Admin dashboard (metrics and health)
- [x] Design system (colors, typography, components)
- [x] Form validation and submission
- [x] Image upload with preview
- [x] Real-time chart rendering
- [x] Authentication token management
- [x] Error handling and user feedback
- [x] Mobile-responsive design
- [x] Privacy-first messaging
- [x] API integration (all endpoints)
- [x] Chart animations and interactivity

## 📝 API Response Examples

### Low Risk Claim
```json
{
  "claim_reference_id": "CLM-2024-00001",
  "fraud_risk_score": 0.15,
  "fraud_risk_level": "LOW",
  "recommendation": "PROCEED",
  "matched_incidents_count": 0,
  "risk_factors": [],
  "explanation": "No suspicious patterns detected. Incident characteristics match legitimate claims.",
  "processing_time_ms": 234
}
```

### Medium Risk Claim
```json
{
  "claim_reference_id": "CLM-2024-00002",
  "fraud_risk_score": 0.58,
  "fraud_risk_level": "MEDIUM",
  "recommendation": "HOLD",
  "matched_incidents_count": 2,
  "risk_factors": [
    "Damaged area coverage inconsistent with reported incident",
    "Similar claims found in same geographic zone",
    "Temporal pattern suggests possible staging"
  ],
  "explanation": "Multiple indicators suggest further investigation recommended.",
  "processing_time_ms": 287
}
```

### Critical Risk Claim
```json
{
  "claim_reference_id": "CLM-2024-00003",
  "fraud_risk_score": 0.92,
  "fraud_risk_level": "CRITICAL",
  "recommendation": "INVESTIGATE",
  "matched_incidents_count": 8,
  "risk_factors": [
    "High similarity to known fraud patterns",
    "Multiple matching incidents in database",
    "Unusual damage distribution",
    "Temporal anomalies detected"
  ],
  "explanation": "Strong indicators of potential fraud. Recommend comprehensive investigation.",
  "processing_time_ms": 312
}
```

## 🚀 Production Deployment

### Steps
1. Verify backend running securely (HTTPS on production)
2. Update `API_BASE_URL` in `.js` files if needed
3. Deploy frontend to CDN or static hosting (AWS S3, Netlify, Vercel)
4. Configure CORS headers appropriately
5. Set up HTTPS certificate
6. Test all workflows end-to-end
7. Monitor performance and errors

### Environment-Specific Configuration
```javascript
// Modify API_BASE_URL based on environment
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.crossinsure.com/api'
  : 'http://localhost:8000/api';
```

## 📞 Support

- Review the [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) for backend details
- Check [README.md](../README.md) for full system documentation
- View browser console for detailed error logs
- Verify backend health at `http://localhost:8000/health`

## 📄 License

Part of CrossInsure AI - Privacy-first Insurance Fraud Detection System

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Status**: Production Ready ✅
