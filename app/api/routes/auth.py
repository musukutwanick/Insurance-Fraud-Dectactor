"""
Authentication API routes.

Endpoints:
- POST /auth/login: User login
- POST /auth/refresh: Refresh authentication token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.core.database import get_db
from app.schemas import UserLoginRequest, TokenResponse, RefreshTokenRequest, DemoLoginRequest
from app.services.auth_service import AuthService
from app.utils.auth import TokenUtils
from app.core.logging_config import get_audit_logger
from app.models import User, UserRole
from sqlalchemy import select
import secrets

router = APIRouter(prefix="/auth", tags=["Authentication"])
audit_logger = get_audit_logger()


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint.
    
    Validates username and password, returns JWT tokens if successful.
    
    Args:
        request: Login credentials (username, password)
        db: Database session
        
    Returns:
        TokenResponse with access_token, refresh_token, and token type
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Authenticate user
    user = await AuthService.authenticate_user(
        db,
        username=request.username,
        password=request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Commit the last_login update
    await db.commit()
    
    # Create tokens
    tokens = AuthService.create_tokens(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
    )


@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh authentication token endpoint.
    
    Validates refresh token and issues new access token.
    
    Args:
        request: RefreshTokenRequest containing refresh_token
        db: Database session
        
    Returns:
        TokenResponse with new access_token and refresh_token
        
    Raises:
        HTTPException: 401 if refresh token is invalid
    """
    # Decode refresh token
    payload = TokenUtils.decode_token(request.refresh_token, token_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(payload.get("sub"))
        username = payload.get("username")
        role = payload.get("role")
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    tokens = TokenUtils.create_tokens(user_id, username, role)
    
    audit_logger.info(f"Token refreshed for user ID: {user_id}")
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
    )


@router.post("/demo-login", response_model=TokenResponse, status_code=200)
async def demo_login(
    request: DemoLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Demo login endpoint (no password).
    
    Creates a company-specific demo user if missing, then returns JWT tokens.
    """
    try:
        company_name = request.company_name.strip()
        if not company_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="company_name is required",
            )

        normalized = "".join(ch for ch in company_name.lower().replace(" ", "_") if ch.isalnum() or ch == "_")
        username = request.username or f"{normalized}_demo"
        email = f"{normalized}@demo.local"

        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            demo_password = secrets.token_urlsafe(16)
            try:
                user = await AuthService.create_user(
                    db,
                    username=username,
                    email=email,
                    password=demo_password,
                    role=UserRole.INSURER,
                    organization_name=company_name,
                )
            except ValueError:
                email = f"{normalized}-{secrets.token_hex(4)}@demo.local"
                user = await AuthService.create_user(
                    db,
                    username=username,
                    email=email,
                    password=demo_password,
                    role=UserRole.INSURER,
                    organization_name=company_name,
                )
        else:
            user.last_login = datetime.now(timezone.utc)
            db.add(user)

        await db.commit()

        tokens = AuthService.create_tokens(user)
        audit_logger.info(f"Demo login for user: {user.username} ({company_name})")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
        )
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.error(f"Demo login failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo login failed: {str(e)}",
        )
