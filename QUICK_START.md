# 🚀 CrossInsure AI - Quick Start Guide

**Get the system running in 5 minutes**

---

## Step 1: Start Backend (2 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with test users
python init_db.py

# Start API server
python -m uvicorn app.main:app --reload
```

**Result**: Backend running at `http://localhost:8000` ✅

---

## Step 2: Start Frontend (1 minute)

**In a new terminal window:**

```bash
# Navigate to frontend
cd frontend

# Start simple HTTP server (Python)
python -m http.server 8080

# OR using Node.js
npx http-server -p 8080
```

**Result**: Frontend available at `http://localhost:8080` ✅

---

## Step 3: Access Dashboards (2 minutes)

### Insurer Dashboard
Open in browser: **`http://localhost:8080/insurer.html`**

**Features:**
- Submit insurance claim
- Upload damage images (up to 5)
- Get instant fraud analysis
- See risk score and recommendation

**Test Workflow:**
1. Fill claim form (incident type, location, description)
2. Drag and drop images
3. Click "Analyze Claim"
4. View fraud risk results

### Admin Dashboard
Open in browser: **`http://localhost:8080/admin.html`**

**Features:**
- View system health status
- Monitor fraud metrics
- See risk distribution charts
- Track incidents by type

**Test Workflow:**
1. View real-time system status
2. Check key metrics (claims, fingerprints)
3. Review risk distribution
4. Watch auto-refresh (every 30 seconds)

---

## Authentication: Getting Your Token

### Option 1: Using cURL

```bash
# Get insurer token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "insurer1", "password": "insurer123"}'

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Copy the `access_token` value and paste it into the dashboard when prompted.

### Option 2: In Browser

The dashboard will **automatically prompt** for token on first load:
1. Run the login curl command above
2. Copy the `access_token`
3. Paste into the frontend prompt
4. Token saved in browser localStorage

### Test Credentials

| User | Username | Password | Role | Purpose |
|------|----------|----------|------|---------|
| Insurer | `insurer1` | `insurer123` | INSURER | Submit claims |
| Admin | `admin` | `admin123` | ADMIN | View metrics |

---

## Test Claim Submission

### Scenario 1: Low Risk ✅

1. **Incident Type**: Auto Collision
2. **Location**: Suburban
3. **Description**: Minor bumper damage, easily repairable
4. **Date**: Today
5. **Images**: 2-3 clear photos of damage

**Expected Result**: 
- Risk Score: **0-30%** (LOW)
- Recommendation: **PROCEED**
- Factors: None or minimal

### Scenario 2: Medium Risk ⚠️

1. **Incident Type**: Property Damage
2. **Location**: Urban
3. **Description**: Water damage to furniture, significant
4. **Date**: Last week
5. **Images**: 4-5 photos with varying clarity

**Expected Result**:
- Risk Score: **30-70%** (MEDIUM)
- Recommendation: **HOLD**
- Factors: Pattern analysis, damage inconsistency

### Scenario 3: High Risk 🔴

1. **Incident Type**: Theft
2. **Location**: Rural
3. **Description**: Complete equipment theft
4. **Date**: 2+ weeks ago
5. **Images**: Photos inconsistent with description

**Expected Result**:
- Risk Score: **70-100%** (HIGH/CRITICAL)
- Recommendation: **INVESTIGATE**
- Factors: Multiple fraud indicators

---

## API Endpoints Quick Reference

### Authentication
```
POST /api/auth/login
Input: {"username": "insurer1", "password": "insurer123"}
Output: {access_token, refresh_token, expires_in}
```

### Claim Analysis
```
POST /api/claims/analyze
Headers: Authorization: Bearer <token>
Input: Form data (incident details + images)
Output: {claim_reference_id, fraud_risk_score, recommendation, etc}
```

### Admin Metrics
```
GET /api/admin/metrics
Headers: Authorization: Bearer <admin_token>
Output: {total_claims, high_risk_count, average_score, etc}
```

### System Health
```
GET /api/admin/system-health
Headers: Authorization: Bearer <admin_token>
Output: {status, database_connected, api_response_time, etc}
```

### Health Check (Public)
```
GET /health
Output: {status, service_name, version}
```

---

## Common Issues & Solutions

### ❌ "Cannot GET /insurer.html"
**Solution**: Make sure you're on correct port
- Frontend should be: `http://localhost:8080`
- Not: `http://localhost:8000`

### ❌ "CORS policy blocked"
**Solution**: Backend must be running
- Check: `http://localhost:8000/health`
- If not running, start backend with `uvicorn app.main:app --reload`

### ❌ "401 Unauthorized"
**Solution**: Token invalid or expired
- Get new token with login endpoint
- Paste into dashboard prompt
- Tokens last 30 minutes

### ❌ "Failed to analyze claim"
**Solution**: Check image files
- JPG or PNG format required
- Under 10MB per image
- Max 5 images per claim
- Check browser console for error

### ❌ "Database error"
**Solution**: Reinitialize database
```bash
cd backend
python init_db.py
```

---

## System Architecture (Visual)

```
User Browser
    │
    ├─→ http://localhost:8080/insurer.html (Claim Dashboard)
    │       │ Upload images
    │       │ Submit form
    │       ↓
    └─→ http://localhost:8080/admin.html (Admin Dashboard)
            │ View metrics
            │ Monitor health
            ↓
    
    Fetch API calls to:
    
    FastAPI Backend (http://localhost:8000)
    ├── POST /api/auth/login
    ├── POST /api/claims/analyze
    ├── GET /api/admin/metrics
    ├── GET /api/admin/system-health
    └── GET /health
           │
           ↓
    
    PostgreSQL Database
    ├── Users (admin, insurer1)
    ├── Claims (submitted)
    ├── Incident Fingerprints (forever stored)
    └── Fraud Analysis Results
```

---

## Color Scheme Guide

### Design System Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Background | #000000 | Primary background (Black) |
| Cards | #F0F8FF | Card backgrounds (Alice Blue) |
| Low Risk | #10B981 | Green - Safe claims |
| Medium Risk | #F59E0B | Amber - Review needed |
| High Risk | #EF4444 | Red - Investigate |
| Critical | #7C3AED | Purple - High alert |

### Visual Indicators

- 🟢 **Green** = Low risk, proceed with confidence
- 🟡 **Amber** = Medium risk, manual review recommended
- 🔴 **Red** = High risk, investigation suggested
- 🟣 **Purple** = Critical risk, escalate immediately

---

## File Structure

```
Insurance Fraud Detector/
├── backend/
│   ├── app/
│   │   ├── core/ (config, database, logging)
│   │   ├── models/ (4 ORM models)
│   │   ├── schemas/ (Pydantic validation)
│   │   ├── services/ (5 business logic services)
│   │   ├── api/ (3 route modules)
│   │   ├── utils/ (auth utilities)
│   │   └── main.py (FastAPI app)
│   ├── requirements.txt
│   ├── init_db.py
│   ├── Dockerfile
│   └── README.md
│
├── frontend/
│   ├── insurer.html (Claim submission)
│   ├── admin.html (System monitoring)
│   ├── styles.css (Design system)
│   ├── insurer.js (Frontend logic)
│   ├── admin.js (Admin logic)
│   └── README.md
│
├── COMPLETE_DELIVERY_SUMMARY.md (This overview)
├── FRONTEND_INTEGRATION.md (Integration guide)
└── [8 additional documentation files]
```

---

## Performance Tips

### For Better Responsiveness
- Close unnecessary browser tabs
- Clear browser cache if charts look wrong
- Use Chrome/Firefox for best performance
- Admin dashboard refreshes every 30 seconds

### For Testing
- Use fresh incognito/private window for token testing
- Check Network tab in DevTools for API calls
- View Console for error messages
- Test with different image sizes

---

## What's Next?

### Immediate Tasks
- [x] ✅ Backend complete
- [x] ✅ Frontend complete
- [x] ✅ Documentation complete
- [x] ✅ Both running locally

### Optional Enhancements
- [ ] Add Gemini AI integration (see IMPLEMENTATION_GUIDE.md)
- [ ] Deploy to production (AWS, Heroku, etc.)
- [ ] Add email notifications
- [ ] Implement claim history tracking
- [ ] Create advanced analytics dashboard

### Production Readiness
- [ ] Update `.env` with production settings
- [ ] Configure HTTPS certificate
- [ ] Set up database backups
- [ ] Configure monitoring and alerting
- [ ] Load testing and optimization

---

## Documentation Map

| Document | Read For | Time |
|----------|----------|------|
| This File | Quick start (5 min) | 5 min |
| frontend/README.md | Frontend details | 10 min |
| QUICK_REFERENCE.md | API endpoints | 5 min |
| IMPLEMENTATION_GUIDE.md | Architecture & design | 20 min |
| README.md (backend) | Full setup guide | 15 min |

---

## Support Resources

### Quick Links
- Backend Health: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc` (Alternative API docs)
- Frontend: `http://localhost:8080`

### Troubleshooting
1. Check `IMPLEMENTATION_GUIDE.md` for architecture questions
2. See `frontend/README.md` for frontend issues
3. Check backend logs for error messages
4. Review `QUICK_REFERENCE.md` for API details

---

## Video Walkthrough (Manual)

### 1. Submit a Claim (3 minutes)
- Open Insurer Dashboard
- Fill form (incident type: Auto Collision)
- Upload 2-3 damage images
- Click "Analyze Claim"
- View risk score and recommendation

### 2. View Admin Metrics (2 minutes)
- Open Admin Dashboard
- Review system health status
- Check API response time
- View key metrics cards
- Observe risk distribution chart
- Watch auto-refresh update data

### 3. Test Multiple Scenarios (5 minutes)
- Submit low-risk claim
- Submit medium-risk claim
- Check admin metrics update
- Verify charts refresh
- Review timestamp updates

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| F12 | Open browser DevTools |
| Ctrl+Shift+N | New incognito window |
| Ctrl+Shift+I | Inspect element |
| Ctrl+L | Focus address bar |
| Ctrl+R | Refresh page |
| Ctrl+Shift+R | Hard refresh (clear cache) |

---

## Token Lifecycle

```
┌─────────────────┐
│  Login Request  │
└────────┬────────┘
         │
         ↓
┌────────────────────────────────────┐
│ Generate Access Token (30 minutes) │
│ Generate Refresh Token (7 days)    │
└────────┬───────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│ Store in Browser localStorage       │
│ Use in: Authorization: Bearer <tok> │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│ Token Valid for 30 Minutes          │
│ After that: Generate New with       │
│ Refresh Token                       │
└─────────────────────────────────────┘
```

---

## Database Schema Overview

```
Users
├── id (PK)
├── username (unique)
├── email
├── hashed_password
├── role (ADMIN/INSURER)
└── timestamps

Claims
├── id (PK)
├── claim_reference_id (anonymized)
├── user_id (FK → Users)
├── incident_type
├── location_zone
├── damage_description
├── incident_date
└── timestamps

IncidentFingerprints
├── id (PK)
├── claim_id (FK → Claims)
├── image_embedding (JSON)
├── text_embedding (JSON)
├── spatial_fingerprint
└── temporal_fingerprint

FraudAnalysisResults
├── id (PK)
├── claim_id (FK → Claims)
├── fraud_risk_score
├── fraud_risk_level
├── recommendation
└── risk_factors (JSON)
```

---

## Success Indicators ✅

You'll know everything is working when:

1. **Backend**
   - ✅ `http://localhost:8000/health` returns `{"status": "healthy"}`
   - ✅ `/docs` shows Swagger UI with all endpoints
   - ✅ Database initialized with test users

2. **Frontend**
   - ✅ `http://localhost:8080/insurer.html` loads without errors
   - ✅ `http://localhost:8080/admin.html` loads without errors
   - ✅ Token prompt appears on page load

3. **Integration**
   - ✅ Can submit claim and see results
   - ✅ Admin dashboard shows metrics
   - ✅ Charts render and refresh
   - ✅ No console errors

---

## 🎉 You're All Set!

Your CrossInsure AI fraud detection system is ready to use.

**Total time to deployment: 5 minutes** ⏱️

---

**Questions?** Check the documentation files for detailed information.

**Ready for production?** See COMPLETE_DELIVERY_SUMMARY.md for deployment checklist.

---

*CrossInsure AI - Privacy-First Insurance Fraud Detection System*  
*Version 1.0.0 • Production Ready*
