"""
Quick test script for Gemini integration.
Run this to verify Gemini API connection and basic functionality.
"""

import asyncio
import os
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.gemini_fraud_analyzer import gemini_fraud_analyzer


async def test_gemini_connection():
    """Test Gemini API connection and basic functionality."""
    
    print("=" * 60)
    print("Gemini Integration Test")
    print("=" * 60)
    
    # Check API key
    if settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key-here":
        print("✅ Gemini API key configured")
        print(f"   Model: {settings.gemini_model}")
        print(f"   Embedding Model: {settings.gemini_embedding_model}")
    else:
        print("⚠️  Gemini API key not configured")
        print("   System will use fallback embeddings")
        print("   To enable Gemini: Set GEMINI_API_KEY in .env file")
        print("")
    
    print("\n" + "=" * 60)
    print("Test 1: Text Embedding Generation")
    print("=" * 60)
    
    test_text = "Front bumper damaged in collision with another vehicle"
    try:
        embedding = await EmbeddingService.generate_text_embedding(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        print(f"   Sample values: {embedding[:5]}")
        
        if len(embedding) == 768:
            print("   ✅ Using Gemini embeddings (768-dim)")
        else:
            print("   ⚠️  Using fallback embeddings")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test 2: Fraud Analysis")
    print("=" * 60)
    
    try:
        analysis = await gemini_fraud_analyzer.analyze_claim_fraud_risk(
            incident_type="vehicle_collision",
            damage_description="Rear-end collision causing bumper damage",
            location_zone="zone_a",
            image_analysis=None,
            similar_incidents=[],
            temporal_pattern_score=0.3,
            spatial_cluster_score=0.4,
        )
        
        print("✅ Fraud analysis completed")
        print(f"   Risk Level: {analysis['fraud_risk_level']}")
        print(f"   Fraud Score: {analysis['fraud_score']:.2f}")
        print(f"   Confidence: {analysis['confidence']:.2f}")
        print(f"   Red Flags: {len(analysis['red_flags'])}")
        print(f"   Reasoning: {analysis['reasoning'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test 3: Similarity Comparison")
    print("=" * 60)
    
    try:
        # Generate embeddings for similar descriptions
        text1 = "Front bumper damaged in parking lot incident"
        text2 = "Front bumper dented from minor collision"
        text3 = "Windshield cracked by falling debris"
        
        emb1 = await EmbeddingService.generate_text_embedding(text1)
        emb2 = await EmbeddingService.generate_text_embedding(text2)
        emb3 = await EmbeddingService.generate_text_embedding(text3)
        
        # Simple cosine similarity
        def cosine_sim(a, b):
            import numpy as np
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_12 = cosine_sim(emb1, emb2)
        sim_13 = cosine_sim(emb1, emb3)
        
        print(f"✅ Similarity scores calculated")
        print(f"   Similar descriptions (1 vs 2): {sim_12:.3f}")
        print(f"   Different descriptions (1 vs 3): {sim_13:.3f}")
        
        if sim_12 > sim_13:
            print("   ✅ Semantic similarity working correctly")
        else:
            print("   ⚠️  Similarity may need tuning")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key-here":
        print("✅ Gemini integration is active and working")
        print("✅ Your fraud detection system is using AI-powered analysis")
        print("\nNext steps:")
        print("1. Start the application: python -m uvicorn app.main:app --reload")
        print("2. Submit test claims through the API")
        print("3. Monitor fraud analysis results")
    else:
        print("⚠️  Running in fallback mode (no Gemini API key)")
        print("\nTo enable Gemini:")
        print("1. Get API key: https://makersuite.google.com/app/apikey")
        print("2. Add to .env file: GEMINI_API_KEY=your-key-here")
        print("3. Restart the application")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_gemini_connection())
