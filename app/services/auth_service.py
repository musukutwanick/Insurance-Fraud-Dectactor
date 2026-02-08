"""
Service layer for user authentication.

Handles:
- User login validation
- User creation
- Password management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserRole
from app.utils.auth import PasswordUtils, TokenUtils
from app.core.logging_config import get_audit_logger
from datetime import datetime, timezone


class AuthService:
    """Service for user authentication operations."""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> User | None:
        """
        Authenticate a user with username and password.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        audit_logger = get_audit_logger()
        
        # Fetch user
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            audit_logger.warning(f"Login attempt with non-existent username: {username}")
            return None
        
        if not user.is_active:
            audit_logger.warning(f"Login attempt with inactive user: {username}")
            return None
        
        # Verify password
        if not PasswordUtils.verify_password(password, user.hashed_password):
            audit_logger.warning(f"Failed login attempt for user: {username}")
            return None
        
        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        
        audit_logger.info(f"Successful login for user: {username} (ID: {user.id})")
        return user

    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.INSURER,
        organization_name: str | None = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            username: Unique username
            email: User email address
            password: Plain text password
            role: User role (ADMIN or INSURER)
            organization_name: Optional organization name
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username or email already exists
        """
        audit_logger = get_audit_logger()
        
        # Check username uniqueness
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ValueError(f"Username {username} already exists")
        
        # Check email uniqueness
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ValueError(f"Email {email} already exists")
        
        # Create new user
        hashed_password = PasswordUtils.hash_password(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            organization_name=organization_name,
            is_active=True,
            is_verified=False,
            updated_at=datetime.now(timezone.utc),
        )
        
        db.add(user)
        await db.flush()  # Get the ID before commit
        
        audit_logger.info(f"New user created: {username} (ID: {user.id}, Role: {role})")
        return user

    @staticmethod
    def create_tokens(user: User) -> dict:
        """
        Create JWT tokens for a user.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with access_token, refresh_token, and expires_in
        """
        return TokenUtils.create_tokens(
            user_id=user.id,
            username=user.username,
            role=user.role.value
        )
