"""
JWT authentication utilities for CrossInsure AI.

Handles:
- Token generation (access and refresh tokens)
- Token validation and decoding
- Password hashing and verification
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
# Use pbkdf2_sha256 for demo stability (bcrypt backend can fail on some setups).
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class PasswordUtils:
    """Utilities for password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)


class TokenUtils:
    """Utilities for JWT token generation and validation."""

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, int]:
        """
        Create a JWT access token.
        
        Args:
            data: Claims to encode in the token
            expires_delta: Optional expiration time delta
            
        Returns:
            Tuple of (token_string, expires_in_seconds)
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        expires_in = int((expire - datetime.now(timezone.utc)).total_seconds())
        return encoded_jwt, expires_in

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> tuple[str, int]:
        """
        Create a JWT refresh token.
        
        Args:
            data: Claims to encode in the token
            
        Returns:
            Tuple of (token_string, expires_in_seconds)
        """
        to_encode = data.copy()
        
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        expires_in = int((expire - datetime.now(timezone.utc)).total_seconds())
        return encoded_jwt, expires_in

    @staticmethod
    def decode_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: The JWT token string
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload, or None if invalid
            
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                return None
                
            return payload
        except JWTError:
            return None

    @staticmethod
    def create_tokens(user_id: int, username: str, role: str) -> Dict[str, Any]:
        """
        Create both access and refresh tokens for a user.
        
        Args:
            user_id: User ID to encode in token
            username: Username to encode in token
            role: User role to encode in token
            
        Returns:
            Dictionary with access_token, refresh_token, and expires_in
        """
        token_data = {
            "sub": str(user_id),
            "username": username,
            "role": role,
        }
        
        access_token, access_expires = TokenUtils.create_access_token(token_data)
        refresh_token, refresh_expires = TokenUtils.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": access_expires,
        }


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class TokenError(Exception):
    """Raised when token validation fails."""
    pass
