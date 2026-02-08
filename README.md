# CrossInsure AI - AI-Powered Insurance Fraud Detection System

A production-grade FastAPI backend for detecting multi-policy insurance fraud by comparing new claims against anonymized historical incident fingerprints. **Now powered by Google Gemini AI!**

## 🚀 New: Google Gemini Integration

The system now features advanced AI capabilities:
- **Semantic Embeddings** - 768-dimensional embeddings using Google's text-embedding-004
- **Vision Analysis** - Automated damage assessment from images using Gemini Vision
- **AI Fraud Detection** - Intelligent risk assessment with detailed reasoning and red flags
- **Smart Fallback** - Continues working even without API access

👉 **[Quick Setup Guide: GEMINI_INTEGRATION_COMPLETE.md](GEMINI_INTEGRATION_COMPLETE.md)**
📖 **[Detailed Setup: GEMINI_SETUP.md](GEMINI_SETUP.md)**

## System Architecture

### Core Principle: Privacy-First Design
- **Raw images and personal data are NEVER stored permanently**
- Only anonymized embeddings and fingerprints are persisted indefinitely
- Enables cross-policy fraud detection while maintaining privacy

### Data Processing Pipeline

```
Insurance Claim
    ↓
[Image Processing]  → Mask sensitive regions (faces, license plates)
                   → Generate perceptual fingerprints
                   → Generate embeddings (Gemini Vision AI)
    ↓
[Text Processing]   → Generate semantic embeddings (Gemini API)
                   → Understand meaning, not just keywords
    ↓
[Fingerprinting]    → Spatio-temporal fingerprint
                   → Incident classification code
    ↓
[Similarity Matching] → AI-powered semantic comparison
                      → Compute similarity scores
    ↓
[AI Risk Analysis]  → Gemini analyzes patterns and anomalies
                   → Identifies specific red flags
                   → Provides detailed reasoning
    ↓
[Storage]           → Store anonymized fingerprint forever
                   → Return analysis results (anonymized)
```

## Tech Stack

- **Framework:** FastAPI 0.104.1
- **Web Server:** Uvicorn
- **Database:** SQLite/PostgreSQL with async SQLAlchemy
- **ORM:** SQLAlchemy 2.0 with async support
- **Authentication:** JWT (PyJWT)
- **Schemas:** Pydantic v2
- **Image Processing:** Pillow, OpenCV, NumPy
- **Password Hashing:** Passlib with bcrypt
- **AI Engine:** Google Gemini 1.5 (Flash/Pro)

## Project Structure

```
insurance_fraud_detector/
├── app/
│   ├── main.py                 # FastAPI application setup
│   ├── __init__.py
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── logging_config.py  # Logging configuration
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py        # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── __init__.py        # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── image_service.py   # Image processing service
│   │   ├── embedding_service.py # Embeddings & fingerprints
│   │   ├── claim_service.py   # Claim processing & orchestration
│   │   └── __init__.py
│   ├── api/
│   │   ├── dependencies.py    # FastAPI dependencies (auth, DB)
│   │   ├── routes/
│   │   │   ├── auth.py        # /auth/* endpoints
│   │   │   ├── claims.py      # /claims/* endpoints
│   │   │   ├── admin.py       # /admin/* endpoints
│   │   │   └── __init__.py
│   │   └── __init__.py
│   └── utils/
│       ├── auth.py            # Token & password utilities
│       └── __init__.py
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## API Endpoints

### Authentication (`/api/auth`)

#### POST `/api/auth/login`
User login with username and password.

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "insurer_user",
    "password": "secure_password_123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST `/api/auth/refresh`
Refresh authentication token.

```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Claims (`/api/claims`)

#### POST `/api/claims/analyze`
Submit claim and perform fraud analysis.

**Request (multipart form):**
```bash
curl -X POST "http://localhost:8000/api/claims/analyze" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "incident_type=motor_damage" \
  -F "damage_description=Vehicle collided at intersection. Severe front-end damage." \
  -F "location_zone=zone_a" \
  -F "incident_date_approx=2024-01-30T14:00:00" \
  -F "incident_time_window_start=2024-01-30T13:00:00" \
  -F "incident_time_window_end=2024-01-30T15:00:00" \
  -F "damage_images=@image1.jpg" \
  -F "damage_images=@image2.jpg"
```

**Incident Types:**
- `motor_damage` - Motor vehicle damage
- `collision` - Vehicle collision
- `theft` - Vehicle/property theft
- `property_damage` - Property damage
- `fire` - Fire damage
- `water_damage` - Water/flooding damage
- `other` - Other incidents

**Location Zones:**
- `zone_a` through `zone_e` - Anonymized geographic zones

**Response:**
```json
{
  "claim_reference_id": "CLM-8f92c7d3-2e1a-4b8c-9d5f",
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
  "risk_factors": [
    "High image similarity to incident from 47 days ago",
    "Location and time pattern matches previous claim"
  ],
  "explanation": "Claim shows elevated fraud risk due to high similarity to a previous claim.",
  "analyzed_at": "2024-01-31T16:45:30Z",
  "processing_time_ms": 2340
}
```

**Fraud Risk Levels:**
- `LOW` (0.0-0.3) → Recommendation: `PROCEED`
- `MEDIUM` (0.3-0.6) → Recommendation: `HOLD`
- `HIGH` (0.6-0.8) → Recommendation: `INVESTIGATE`
- `CRITICAL` (0.8-1.0) → Recommendation: `INVESTIGATE`

### Admin Monitoring (`/api/admin`)

#### GET `/api/admin/metrics`
Get system metrics and statistics.

```bash
curl -X GET "http://localhost:8000/api/admin/metrics" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
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

#### GET `/api/admin/system-health`
Get system health status.

```bash
curl -X GET "http://localhost:8000/api/admin/system-health" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
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

## Database Models

### User
- Stores user credentials and role information
- Roles: `ADMIN`, `INSURER`
- No personal information stored

### Claim
- Insurance claim submission record
- Contains: claim reference ID, incident type, description, location zone, time window
- Raw images and personal details are NOT stored here

### IncidentFingerprint
**The core of the fraud detection system**
- Stores ONLY anonymized data:
  - Text embedding (from damage description)
  - Image embedding (from damage images)
  - Spatial fingerprint (location hash)
  - Temporal fingerprint (time window hash)
  - Incident type code
  - Damage severity score
- Persisted indefinitely for future comparisons
- No raw images, policy numbers, or personal identifiers

### FraudAnalysisResult
- Results of fraud analysis
- Stores similarity scores and matched fingerprints
- Contains recommendation and risk factors
- Analyst notes for investigations

## Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 13+

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/crossinsure-ai.git
cd crossinsure-ai
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env

# Edit .env with your configuration
# - Database URL (PostgreSQL)
# - JWT secret key
# - API settings
```

### 5. Initialize Database
```bash
# The database will auto-initialize on first run
# Or manually create tables (optional):
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 6. Create Test Admin User
```bash
# Use the Python shell to create a test user
python -c "
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, UserRole
from app.utils.auth import PasswordUtils

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.username == 'admin'))
        if result.scalar_one_or_none():
            print('Admin user already exists')
            return
        
        user = User(
            username='admin',
            email='admin@example.com',
            hashed_password=PasswordUtils.hash_password('admin123'),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        await db.commit()
        print('Admin user created: admin / admin123')

asyncio.run(create_admin())
"
```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Using the Task
```bash
# Windows PowerShell with create_and_run_task
# (If you have a tasks.json configured)
```

Access the application:
- API: http://localhost:8000/
- API Documentation: http://localhost:8000/api/docs
- Alternative Docs: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/health

## API Documentation

Interactive API documentation is auto-generated and available at:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

## Integration with AI Services

### Placeholder for Gemini Embeddings API

The embedding service is currently a placeholder implementation using hash-based embeddings.

To integrate Google Gemini Embeddings API:

1. Install the Gemini API client:
```bash
pip install google-generativeai
```

2. Update `app/services/embedding_service.py`:

```python
import google.generativeai as genai

async def generate_text_embedding(text: str) -> List[float]:
    """Generate text embedding using Gemini API."""
    genai.configure(api_key=settings.gemini_api_key)
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="SEMANTIC_SIMILARITY"
    )
    return result['embedding']

async def generate_image_embedding(image_bytes: bytes) -> List[float]:
    """Generate image embedding using Gemini Multimodal API."""
    genai.configure(api_key=settings.gemini_api_key)
    # Use multimodal embedding for images
    # Implementation depends on Gemini's image handling
```

3. Update `.env`:
```
GEMINI_API_KEY=your-api-key-here
```

## Logging & Audit Trail

The system maintains comprehensive logging:

- **Application Logs:** `logs/crossinsure_ai.log`
  - System events, errors, and debug information
  - Rotated at 10 MB, keeps 5 backups

- **Audit Logs:** `logs/audit_trail.log`
  - User authentication events
  - Claim submissions and analysis
  - Admin actions
  - For compliance and investigation

Access logs:
```bash
tail -f logs/crossinsure_ai.log
tail -f logs/audit_trail.log
```

## Security Considerations

1. **Environment Variables:** Store sensitive data in `.env`, never in code
2. **JWT Secret:** Use a strong random secret key in production
3. **CORS:** Configure allowed origins for your deployment
4. **HTTPS:** Always use HTTPS in production
5. **Database:** Use strong credentials and limit network access
6. **Rate Limiting:** Consider adding rate limiting for production
7. **Input Validation:** All inputs are validated via Pydantic schemas
8. **SQL Injection:** Using SQLAlchemy ORM prevents SQL injection
9. **Password Hashing:** All passwords hashed with bcrypt

## Docker Deployment

### Build Docker Image
```bash
docker build -t crossinsure-ai:latest .
```

### Run Container
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:password@db:5432/insurance_fraud_db" \
  -e SECRET_KEY="your-secret-key" \
  -e ENVIRONMENT="production" \
  crossinsure-ai:latest
```

### Docker Compose (with PostgreSQL)
```bash
docker-compose up -d
```

See `Dockerfile` and `docker-compose.yml` for full configuration.

## Testing

### Manual API Testing with curl

1. **Login:**
```bash
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
```

2. **Submit Claim:**
```bash
curl -X POST http://localhost:8000/api/claims/analyze \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "incident_type=motor_damage" \
  -F "damage_description=Vehicle hit from rear at traffic light. Moderate trunk damage." \
  -F "location_zone=zone_a" \
  -F "incident_date_approx=2024-01-31T14:00:00" \
  -F "incident_time_window_start=2024-01-31T13:00:00" \
  -F "incident_time_window_end=2024-01-31T15:00:00"
```

3. **Check Metrics:**
```bash
curl -X GET http://localhost:8000/api/admin/metrics \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Performance Optimization

- **Database Indexing:** All frequently queried fields are indexed
- **Async Operations:** All I/O operations are async (database, images)
- **Connection Pooling:** SQLAlchemy handles connection pooling
- **Image Compression:** Images are validated and processed efficiently
- **Batch Processing:** Can handle concurrent claim submissions

## Future Enhancements

1. **Gemini Integration:** Replace placeholder embeddings with actual Gemini API
2. **Advanced Image Processing:**
   - YOLOv8 for object detection (license plates, VINs)
   - MediaPipe for face detection and masking
   - Advanced perceptual hashing

3. **ML Model Enhancement:**
   - Train custom models on historical claims data
   - Implement temporal decay (older incidents weighted less)
   - Multi-modal learning combining images + text

4. **Performance:**
   - Implement caching (Redis) for frequently accessed fingerprints
   - Vectorstore (Pinecone, Weaviate) for efficient similarity search
   - Batch processing for high-volume claims

5. **Analytics:**
   - Dashboard for fraud trends
   - Reporting and export capabilities
   - Pattern analysis and insights

6. **Integration:**
   - Webhook support for external systems
   - Batch API for processing multiple claims
   - Integration with claim management systems

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential. All rights reserved.

## Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Contact the development team
- Check documentation at http://localhost:8000/api/docs

## Changelog

### Version 1.0.0 (Initial Release)
- Core API endpoints (auth, claims, admin)
- SQLAlchemy async ORM models
- JWT authentication
- Placeholder AI embedding service
- Image processing pipeline
- Fraud risk scoring
- Admin monitoring
- Comprehensive logging
