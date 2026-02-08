"""
Database initialization and seeding script.

Creates admin user and sample data for testing.
"""

import asyncio
from app.core.database import AsyncSessionLocal, init_db
from app.models import User, UserRole
from app.utils.auth import PasswordUtils


async def create_default_users():
    """Create default admin and test users."""
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # Check if admin exists
        stmt = select(User).where(User.username == "admin")
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin_user = User(
                username="admin",
                email="admin@crossinsure.ai",
                hashed_password=PasswordUtils.hash_password("admin123"),
                role=UserRole.ADMIN,
                organization_name="CrossInsure AI",
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            print("✓ Created admin user: admin / admin123")
        else:
            print("✓ Admin user already exists")
        
        # Check if test insurer exists
        stmt = select(User).where(User.username == "insurer1")
        result = await db.execute(stmt)
        insurer = result.scalar_one_or_none()
        
        if not insurer:
            insurer_user = User(
                username="insurer1",
                email="user@abc-insurance.com",
                hashed_password=PasswordUtils.hash_password("insurer123"),
                role=UserRole.INSURER,
                organization_name="ABC Insurance",
                is_active=True,
                is_verified=True,
            )
            db.add(insurer_user)
            print("✓ Created insurer user: insurer1 / insurer123")
        else:
            print("✓ Insurer user already exists")
        
        await db.commit()


async def main():
    """Initialize database and create default users."""
    print("Initializing CrossInsure AI Database...")
    print("-" * 50)
    
    try:
        # Initialize database tables
        print("Creating database tables...")
        await init_db()
        print("✓ Database tables created/verified")
        
        # Create default users
        print("\nCreating default users...")
        await create_default_users()
        
        print("\n" + "=" * 50)
        print("✓ Database initialization complete!")
        print("\nTest Credentials:")
        print("  Admin: admin / admin123")
        print("  Insurer: insurer1 / insurer123")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
