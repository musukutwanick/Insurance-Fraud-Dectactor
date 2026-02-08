# CrossInsure AI - Implementation Guide

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL connection string
```

### 3. Initialize Database
```bash
python init_db.py
```

Output:
```
✓ Database initialization complete!

Test Credentials:
  Admin: admin / admin123
  Insurer: insurer1 / insurer123
```

### 4. Run Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test API
```bash
# Open browser
http://localhost:8000/api/docs

# Or use curl
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## Architecture Overview

### Data Flow

```
┌─────────────────┐
│ Insurance Claim │
│   Submission    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Image Processing Layer      │
│ - Mask sensitive regions    │
│ - Validate format/size      │
│ - Generate fingerprints     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Embedding Generation        │
│ - Text embeddings           │
│ - Image embeddings          │
│ (Placeholder for Gemini)    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Fingerprinting              │
│ - Spatial fingerprint       │
│ - Temporal fingerprint      │
│ - Incident classification   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Historical Comparison       │
│ - Query incident store      │
│ - Compute similarity        │
│ - Find matches              │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Fraud Risk Scoring          │
│ - Calculate risk score      │
│ - Assign risk level         │
│ - Generate recommendation   │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Storage                     │
│ - Store fingerprint forever │
│ - Store analysis results    │
│ - Return anonymized claim   │
│   reference ID              │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│ Analysis Result │
│ Returned to API │
└─────────────────┘
```

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- 'ADMIN', 'INSURER'
  organization_name VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP
);
```

#### Claims Table
```sql
CREATE TABLE claims (
  id SERIAL PRIMARY KEY,
  claim_reference_id VARCHAR(255) UNIQUE NOT NULL,
  user_id INTEGER REFERENCES users(id),
  incident_type VARCHAR(255) NOT NULL,
  location_zone VARCHAR(255) NOT NULL,
  damage_description TEXT NOT NULL,
  incident_date_approx TIMESTAMP NOT NULL,
  incident_time_window_start TIMESTAMP NOT NULL,
  incident_time_window_end TIMESTAMP NOT NULL,
  image_count INTEGER DEFAULT 0,
  is_processed BOOLEAN DEFAULT FALSE,
  processing_error TEXT,
  submitted_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### IncidentFingerprints Table (Core Storage)
```sql
CREATE TABLE incident_fingerprints (
  id SERIAL PRIMARY KEY,
  claim_id INTEGER REFERENCES claims(id),
  claim_reference_id VARCHAR(255) UNIQUE NOT NULL,
  image_embedding JSON NOT NULL,        -- Vector array
  text_embedding JSON NOT NULL,         -- Vector array
  spatial_fingerprint VARCHAR(255) NOT NULL,
  temporal_fingerprint VARCHAR(255) NOT NULL,
  incident_type_code VARCHAR(50) NOT NULL,
  damage_severity_score FLOAT NOT NULL,
  embedding_model_version VARCHAR(50),
  stored_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### FraudAnalysisResults Table
```sql
CREATE TABLE fraud_analysis_results (
  id SERIAL PRIMARY KEY,
  claim_id INTEGER REFERENCES claims(id),
  matched_fingerprint_id INTEGER REFERENCES incident_fingerprints(id),
  overall_fraud_risk_score FLOAT NOT NULL,
  fraud_risk_level VARCHAR(50) NOT NULL,
  recommendation VARCHAR(50) NOT NULL,
  image_similarity_score FLOAT,
  text_similarity_score FLOAT,
  temporal_similarity_score FLOAT,
  spatial_similarity_score FLOAT,
  matched_fingerprint_count INTEGER DEFAULT 0,
  top_match_details JSON,
  similarity_breakdown JSON,
  risk_factors JSON,
  explanation TEXT,
  analyst_notes TEXT,
  reviewed_by_admin BOOLEAN DEFAULT FALSE,
  analyzed_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints Reference

### Authentication

#### POST /api/auth/login
**Login user and get JWT tokens**

Request:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/auth/refresh
**Refresh authentication token**

Request:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Claims Processing

#### POST /api/claims/analyze
**Submit claim and perform fraud analysis**

Content-Type: `multipart/form-data`

Form Fields:
- `incident_type` (required): motor_damage, collision, theft, property_damage, fire, water_damage, other
- `damage_description` (required): Text description of damage
- `location_zone` (required): zone_a, zone_b, zone_c, zone_d, zone_e
- `incident_date_approx` (required): ISO datetime string
- `incident_time_window_start` (required): ISO datetime string
- `incident_time_window_end` (required): ISO datetime string
- `damage_images` (optional): 1-5 image files

Response:
```json
{
  "claim_reference_id": "CLM-8f92c7d3",
  "analysis_status": "completed",
  "fraud_risk_score": 0.72,
  "fraud_risk_level": "HIGH",
  "recommendation": "INVESTIGATE",
  "matched_incidents_count": 3,
  "top_match": {
    "matched_fingerprint_id": 15,
    "similarity_score": 0.86,
    "matched_incident_type": "motor_damage",
    "matched_incident_date": "2023-12-15T14:30:00Z",
    "days_since_matched_incident": 47,
    "similarity_breakdown": {
      "image_similarity": 0.87,
      "text_similarity": 0.72,
      "temporal_similarity": 0.91,
      "spatial_similarity": 0.85
    }
  },
  "risk_factors": ["High image similarity to incident from 47 days ago"],
  "explanation": "Claim shows elevated fraud risk...",
  "analyzed_at": "2024-01-31T16:45:30Z",
  "processing_time_ms": 2340
}
```

### Admin Monitoring

#### GET /api/admin/metrics
**Get system metrics and statistics**

Headers: `Authorization: Bearer {admin_token}`

Response:
```json
{
  "total_claims_analyzed": 1250,
  "total_fingerprints_stored": 1189,
  "high_risk_fraud_count": 145,
  "medium_risk_fraud_count": 287,
  "low_risk_fraud_count": 818,
  "claims_analyzed_today": 23,
  "claims_analyzed_this_week": 156,
  "claims_analyzed_this_month": 487,
  "average_fraud_risk_score": 0.38,
  "most_common_risk_factor": "Image similarity to historical incident",
  "fingerprints_added_today": 20,
  "timestamp": "2024-01-31T16:50:00Z"
}
```

#### GET /api/admin/system-health
**Get system health status**

Headers: `Authorization: Bearer {admin_token}`

Response:
```json
{
  "status": "healthy",
  "database_connected": true,
  "api_response_time_ms": 45,
  "timestamp": "2024-01-31T16:50:00Z",
  "components": {
    "database": "healthy",
    "cache": "healthy",
    "ai_service": "pending"
  }
}
```

---

## Integration with Gemini AI

### Current State
The system uses **placeholder embeddings** based on hashing. This allows immediate deployment and testing.

### To Integrate Gemini API

#### Step 1: Install Gemini Client
```bash
pip install google-generativeai
```

#### Step 2: Update Configuration
In `.env`:
```
GEMINI_API_KEY=your-api-key-here
```

#### Step 3: Modify Embedding Service
Replace placeholder in `app/services/embedding_service.py`:

```python
import google.generativeai as genai

class EmbeddingService:
    @staticmethod
    async def generate_text_embedding(text: str) -> List[float]:
        """Generate text embedding using Gemini API."""
        genai.configure(api_key=settings.gemini_api_key)
        
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="SEMANTIC_SIMILARITY"
        )
        
        return result['embedding']
    
    @staticmethod
    async def generate_image_embedding(image_bytes: bytes) -> List[float]:
        """Generate image embedding using Gemini Multimodal API."""
        genai.configure(api_key=settings.gemini_api_key)
        
        # Convert bytes to base64
        import base64
        image_b64 = base64.b64encode(image_bytes).decode()
        
        result = genai.embed_content(
            model="models/multimodal-embedding-001",
            content=[
                {
                    "mime_type": "image/jpeg",
                    "data": image_b64
                }
            ],
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        return result['embedding']
```

#### Step 4: Test Integration
```bash
# Run init_db to create test user
python init_db.py

# Start server
uvicorn app.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/api/claims/analyze \
  -H "Authorization: Bearer {token}" \
  -F "incident_type=motor_damage" \
  -F "damage_description=Test claim" \
  -F "location_zone=zone_a" \
  -F "incident_date_approx=2024-01-31T14:00:00" \
  -F "incident_time_window_start=2024-01-31T13:00:00" \
  -F "incident_time_window_end=2024-01-31T15:00:00"
```

---

## Performance Optimization

### Database Optimization
- All frequently queried columns are indexed
- Connection pooling configured (pool_size=20, max_overflow=0)
- Async operations prevent blocking

### Caching Strategies (Future)
```python
# Redis caching for hot fingerprints
from redis import asyncio as aioredis

cache = aioredis.from_url("redis://localhost")

# Cache similar incidents lookup
await cache.set(
    f"similar_incidents:{fingerprint_id}",
    json.dumps(matches),
    ex=3600  # 1 hour
)
```

### Batch Processing (Future)
```python
# Process multiple claims concurrently
from concurrent.futures import ProcessPoolExecutor

async def batch_analyze_claims(claims: List[Dict]):
    """Process multiple claims in parallel."""
    tasks = [
        ClaimProcessingService.submit_and_analyze_claim(
            db, user, **claim
        )
        for claim in claims
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Security Best Practices

### 1. Environment Secrets
```bash
# Never commit .env
git add .gitignore
echo ".env" >> .gitignore

# Use strong secret keys in production
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

### 2. Database Security
```sql
-- Create minimal-privilege user
CREATE ROLE insurance_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE insurance_fraud_db TO insurance_app;
GRANT USAGE ON SCHEMA public TO insurance_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO insurance_app;
```

### 3. API Authentication
- JWT tokens expire after 30 minutes (configurable)
- Refresh tokens valid for 7 days
- All passwords hashed with bcrypt (cost factor 12)

### 4. Data Privacy
- No raw images stored permanently
- No personal identifiers in fingerprints
- Anonymized claim reference IDs
- Audit logging of all sensitive operations

### 5. HTTPS
```bash
# Use SSL/TLS in production
# Option 1: Nginx reverse proxy
# Option 2: Uvicorn with SSL
uvicorn app.main:app \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

---

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server
```

**Solution:**
1. Verify PostgreSQL is running
2. Check DATABASE_URL in .env
3. Verify credentials:
   ```bash
   psql -U insurance_user -d insurance_fraud_db -h localhost
   ```

### JWT Token Expired
```
HTTPException: Could not validate credentials
```

**Solution:**
Use the `/api/auth/refresh` endpoint with your refresh token:
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJhbGc..."}'
```

### Image Upload Fails
```
Error: Image exceeds maximum size of 10 MB
```

**Solution:**
Compress images before upload or increase limit in `image_service.py`

### Slow Claim Analysis
Check:
1. Database query performance
2. Number of historical fingerprints to compare
3. Network latency (if using remote Gemini API)

Optimize by:
- Adding database indexes
- Implementing fingerprint caching
- Batch processing similar-risk claims

---

## Testing Workflow

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "insurer1",
    "password": "insurer123"
  }'
```

Save `access_token` from response.

### 2. Submit First Claim
```bash
curl -X POST http://localhost:8000/api/claims/analyze \
  -H "Authorization: Bearer {access_token}" \
  -F "incident_type=motor_damage" \
  -F "damage_description=Vehicle damaged in collision." \
  -F "location_zone=zone_a" \
  -F "incident_date_approx=2024-01-31T14:00:00" \
  -F "incident_time_window_start=2024-01-31T13:00:00" \
  -F "incident_time_window_end=2024-01-31T15:00:00"
```

### 3. Submit Similar Claim
```bash
# Similar description, same zone → should match previous
curl -X POST http://localhost:8000/api/claims/analyze \
  -H "Authorization: Bearer {access_token}" \
  -F "incident_type=motor_damage" \
  -F "damage_description=Vehicle damaged in collision at same intersection." \
  -F "location_zone=zone_a" \
  -F "incident_date_approx=2024-01-29T14:00:00" \
  -F "incident_time_window_start=2024-01-29T13:00:00" \
  -F "incident_time_window_end=2024-01-29T15:00:00"
```

Expected: High fraud risk due to similarity.

### 4. View Metrics
```bash
curl -X GET http://localhost:8000/api/admin/metrics \
  -H "Authorization: Bearer {admin_access_token}"
```

---

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t crossinsure:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crossinsure-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crossinsure-api
  template:
    metadata:
      labels:
        app: crossinsure-api
    spec:
      containers:
      - name: api
        image: crossinsure:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: crossinsure-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: crossinsure-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## Support & Documentation

- **API Documentation:** http://localhost:8000/api/docs
- **GitHub Issues:** Create issue on repository
- **Email:** support@crossinsure.ai
- **Slack:** #crossinsure-ai channel

---

## Version History

### v1.0.0 (Current)
- Core API endpoints (auth, claims, admin)
- SQLAlchemy async ORM
- JWT authentication
- Placeholder embedding service
- Image processing pipeline
- Comprehensive logging

### Planned for v2.0
- Gemini API integration
- Advanced image processing (YOLOv8, MediaPipe)
- Redis caching
- Webhook support
- Batch processing API
- Web dashboard
