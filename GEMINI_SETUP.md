# Google Gemini Integration Guide

## Overview
Your Insurance Fraud Detector is now integrated with Google Gemini AI for:
- **Intelligent text embeddings** using Gemini's text-embedding-004 model
- **Vision-based image analysis** for damage assessment
- **AI-powered fraud detection** with detailed reasoning
- **Automatic fallback** to heuristic analysis if Gemini is unavailable

## Setup Instructions

### 1. Get Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Configure Your Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your-actual-api-key-here
   ```

3. (Optional) Adjust Gemini model settings:
   ```env
   # Use flash for faster, cheaper processing
   GEMINI_MODEL=gemini-1.5-flash
   
   # Or use pro for higher quality (more expensive)
   # GEMINI_MODEL=gemini-1.5-pro
   
   GEMINI_TEMPERATURE=0.7
   GEMINI_MAX_TOKENS=8192
   ```

### 3. Install Dependencies

Install the updated requirements including Gemini SDK:

```bash
pip install -r requirements.txt
```

This will install:
- `google-generativeai` - Official Gemini Python SDK
- `aiofiles` - For async file operations
- Plus all existing dependencies

### 4. Test the Integration

Run the application:

```bash
python -m uvicorn app.main:app --reload
```

The system will:
- ✅ Use Gemini embeddings if API key is configured
- ✅ Automatically fall back to hash-based embeddings if unavailable
- ✅ Log connection status on startup

Check the logs for:
```
INFO: Gemini API configured successfully
INFO: Gemini fraud analyzer initialized with model: gemini-1.5-flash
```

## Features Enabled

### 1. Intelligent Text Embeddings
- **Model**: `text-embedding-004` (768 dimensions)
- **Use Case**: Semantic similarity of damage descriptions
- **Benefit**: More accurate matching of similar incidents

### 2. Vision-Based Image Analysis
- **Model**: `gemini-1.5-flash` or `gemini-1.5-pro`
- **Use Case**: Automated damage image assessment
- **Process**:
  1. Gemini analyzes the damage image
  2. Generates detailed description
  3. Converts description to embedding
- **Benefit**: Understand image content without manual labeling

### 3. AI-Powered Fraud Analysis
- **Model**: `gemini-1.5-flash` or `gemini-1.5-pro`
- **Analyzes**:
  - Damage description patterns
  - Temporal anomalies
  - Spatial clustering
  - Similar historical incidents
- **Outputs**:
  - Risk level (LOW/MEDIUM/HIGH/CRITICAL)
  - Confidence score
  - Specific red flags
  - Detailed reasoning
  - Actionable recommendations

### 4. Automatic Fallback
If Gemini API is unavailable or rate-limited:
- System uses hash-based embeddings
- Heuristic fraud scoring kicks in
- Application continues to function
- Lower confidence scores indicated

## API Costs

**Gemini 1.5 Flash** (Recommended for production):
- Text: $0.00001875 per 1K characters
- Images: $0.00001875 per image
- Embeddings: $0.00001 per 1K tokens

**Gemini 1.5 Pro** (Higher quality):
- Text: $0.00125 per 1K characters
- Images: $0.0025 per image
- About 100x more expensive than Flash

**Estimated Cost per Claim**:
- With Flash: ~$0.0001-0.0005 per claim
- With Pro: ~$0.01-0.05 per claim

## Model Selection Guide

### Use Gemini 1.5 Flash when:
- ✅ Processing high volumes of claims
- ✅ Need fast response times
- ✅ Cost efficiency is important
- ✅ Standard fraud detection quality is sufficient

### Use Gemini 1.5 Pro when:
- ✅ Need highest accuracy
- ✅ Complex fraud patterns
- ✅ Handling high-value claims
- ✅ Quality over cost

## Environment Variables Reference

```env
# Required
GEMINI_API_KEY=your-api-key-here

# Optional - Model Selection
GEMINI_MODEL=gemini-1.5-flash              # Text/fraud analysis model
GEMINI_EMBEDDING_MODEL=models/text-embedding-004  # Embedding model
GEMINI_VISION_MODEL=gemini-1.5-flash       # Image analysis model

# Optional - Generation Parameters
GEMINI_TEMPERATURE=0.7      # Creativity (0.0-1.0, lower = more focused)
GEMINI_MAX_TOKENS=8192      # Max response length
```

## Testing the Integration

### Test Text Embeddings

```python
from app.services.embedding_service import EmbeddingService

# Generate embedding
embedding = await EmbeddingService.generate_text_embedding(
    "Front bumper damaged in collision"
)

print(f"Embedding dimension: {len(embedding)}")  # Should be 768 for Gemini
```

### Test Fraud Analysis

Submit a claim through the API and check the response:

```json
{
  "fraud_risk_level": "MEDIUM",
  "fraud_score": 0.65,
  "confidence": 0.85,
  "red_flags": [
    "Multiple similar incidents in same area",
    "Unusual timing pattern"
  ],
  "reasoning": "The claim shows moderate risk due to clustering...",
  "recommendations": [
    "Request additional documentation",
    "Verify incident location"
  ]
}
```

## Troubleshooting

### Error: "API key not configured"
- Check your `.env` file has `GEMINI_API_KEY=...`
- Restart the application after adding the key

### Error: "Resource exhausted" or rate limit
- You've hit API quota limits
- System will fall back to heuristic analysis
- Consider upgrading your Gemini API quota

### Low quality results
- Try switching to `gemini-1.5-pro`
- Adjust `GEMINI_TEMPERATURE` (lower = more focused)
- Check your prompts in `gemini_fraud_analyzer.py`

### High costs
- Switch to `gemini-1.5-flash`
- Reduce `GEMINI_MAX_TOKENS`
- Implement caching for repeated queries

## Security Best Practices

1. **Never commit `.env` file** - it contains your API key
2. **Use environment-specific keys** - different keys for dev/staging/prod
3. **Monitor API usage** - track costs in Google Cloud Console
4. **Rotate keys regularly** - regenerate API keys periodically
5. **Set up billing alerts** - get notified of unexpected usage

## Next Steps

1. ✅ Get your Gemini API key
2. ✅ Configure `.env` file
3. ✅ Install dependencies
4. ✅ Test with sample claims
5. ✅ Monitor logs for Gemini connection status
6. ✅ Review fraud analysis results
7. ✅ Tune parameters based on your needs

## Support

- **Gemini Documentation**: https://ai.google.dev/docs
- **API Reference**: https://ai.google.dev/api
- **Pricing**: https://ai.google.dev/pricing
- **Google AI Studio**: https://makersuite.google.com

---

**Note**: The system works without Gemini API key (using fallback mode), but you'll get significantly better fraud detection results with Gemini enabled.
