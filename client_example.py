"""
API Client Example - CrossInsure AI

This script demonstrates how to interact with the CrossInsure AI API
for testing and integration purposes.
"""

import httpx
import asyncio
import json
from datetime import datetime, timedelta, timezone


class CrossInsureClient:
    """Client for interacting with CrossInsure AI API."""

    def __init__(self, base_url: str = "http://localhost:8000", username: str = None, password: str = None):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.access_token = None
        self.refresh_token = None
        self.username = username
        self.password = password

    async def login(self, username: str = None, password: str = None):
        """Login and obtain access token."""
        user = username or self.username
        pwd = password or self.password
        
        if not user or not pwd:
            raise ValueError("Username and password required")

        response = await self.client.post(
            "/api/auth/login",
            json={"username": user, "password": pwd}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        
        print(f"✓ Logged in as {user}")
        return data

    async def refresh_access_token(self):
        """Refresh the access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        response = await self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        
        print("✓ Access token refreshed")
        return data

    async def submit_claim(
        self,
        incident_type: str,
        damage_description: str,
        location_zone: str,
        incident_date_approx: datetime,
        incident_time_window_start: datetime,
        incident_time_window_end: datetime,
        image_files: list = None,
    ):
        """Submit a claim for fraud analysis."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call login() first.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Prepare form data
        data = {
            "incident_type": incident_type,
            "damage_description": damage_description,
            "location_zone": location_zone,
            "incident_date_approx": incident_date_approx.isoformat(),
            "incident_time_window_start": incident_time_window_start.isoformat(),
            "incident_time_window_end": incident_time_window_end.isoformat(),
        }
        
        # Prepare files
        files = {}
        if image_files:
            for i, image_path in enumerate(image_files):
                with open(image_path, "rb") as f:
                    files[f"damage_images"] = (f"image_{i}.jpg", f, "image/jpeg")

        response = await self.client.post(
            "/api/claims/analyze",
            data=data,
            files=files if files else None,
            headers=headers,
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"✓ Claim submitted: {result['claim_reference_id']}")
        print(f"  Fraud Risk: {result['fraud_risk_level']} ({result['fraud_risk_score']:.0%})")
        print(f"  Recommendation: {result['recommendation']}")
        
        return result

    async def get_metrics(self):
        """Get system metrics (admin only)."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call login() first.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = await self.client.get(
            "/api/admin/metrics",
            headers=headers,
        )
        response.raise_for_status()
        
        data = response.json()
        print("✓ System Metrics:")
        print(f"  Total Claims: {data['total_claims_analyzed']}")
        print(f"  Total Fingerprints: {data['total_fingerprints_stored']}")
        print(f"  High Risk Count: {data['high_risk_fraud_count']}")
        
        return data

    async def get_health(self):
        """Check system health."""
        response = await self.client.get("/health")
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ System Status: {data['status']}")
        
        return data

    async def close(self):
        """Close the client."""
        await self.client.aclose()


async def example_workflow():
    """Example workflow: Login, submit claims, check metrics."""
    
    # Initialize client
    client = CrossInsureClient(
        base_url="http://localhost:8000",
        username="admin",
        password="admin123"
    )
    
    try:
        # Check health
        print("\n=== System Health ===")
        await client.get_health()
        
        # Login
        print("\n=== Authentication ===")
        await client.login()
        
        # Submit a claim (without images for this example)
        print("\n=== Submit Claim ===")
        now = datetime.now(timezone.utc)
        
        analysis_result = await client.submit_claim(
            incident_type="motor_damage",
            damage_description="Vehicle collided with another car at intersection. Significant front-end damage, hood crumpled, windshield broken.",
            location_zone="zone_a",
            incident_date_approx=now - timedelta(days=1),
            incident_time_window_start=now - timedelta(days=1, hours=1),
            incident_time_window_end=now - timedelta(days=1, hours=-1),
        )
        
        # Print analysis results
        print("\n=== Analysis Results ===")
        print(json.dumps(analysis_result, indent=2, default=str))
        
        # Get admin metrics
        print("\n=== System Metrics ===")
        await client.get_metrics()
        
        # Refresh token
        print("\n=== Token Refresh ===")
        await client.refresh_access_token()
        
    finally:
        await client.close()


async def example_multiple_claims():
    """Submit multiple test claims."""
    
    client = CrossInsureClient(username="admin", password="admin123")
    
    try:
        await client.login()
        
        # List of test claims
        test_claims = [
            {
                "incident_type": "motor_damage",
                "description": "Rear-end collision at traffic light.",
                "zone": "zone_a",
            },
            {
                "incident_type": "collision",
                "description": "Side-impact collision in parking lot.",
                "zone": "zone_b",
            },
            {
                "incident_type": "property_damage",
                "description": "Hail damage to roof and windshield.",
                "zone": "zone_c",
            },
        ]
        
        now = datetime.now(timezone.utc)
        
        for i, claim in enumerate(test_claims):
            print(f"\n--- Claim {i+1} ---")
            
            result = await client.submit_claim(
                incident_type=claim["incident_type"],
                damage_description=claim["description"],
                location_zone=claim["zone"],
                incident_date_approx=now - timedelta(days=i),
                incident_time_window_start=now - timedelta(days=i, hours=2),
                incident_time_window_end=now - timedelta(days=i),
            )
            
            # Print key results
            print(f"Risk Score: {result['fraud_risk_score']:.2f}")
            print(f"Risk Level: {result['fraud_risk_level']}")
            print(f"Matched Incidents: {result['matched_incidents_count']}")
        
        # Get final metrics
        print("\n=== Final Metrics ===")
        await client.get_metrics()
        
    finally:
        await client.close()


if __name__ == "__main__":
    # Run example workflow
    print("CrossInsure AI - API Client Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # Basic workflow
    asyncio.run(example_workflow())
    
    # Or run multiple claims
    # asyncio.run(example_multiple_claims())
