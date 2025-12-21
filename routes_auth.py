"""
Authentication and Dashboard Routes for Basalt SaaS
Add these routes to main.py or import this module
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from database import get_db, User, APIKey, Notarization, PRICING_TIERS, init_db
from auth import hash_password, verify_password, create_access_token, decode_access_token, generate_api_key

router = APIRouter()

# Initialize database on import
init_db()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from session cookie"""
    token = request.cookies.get("session")
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("user_id")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Require authenticated user or redirect to login"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


# =============================================================================
# AUTH PAGES
# =============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create session token
    token = create_access_token({"user_id": user.id, "email": user.email})
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax"
    )
    return response


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
async def signup_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    company: str = Form(None),
    db: Session = Depends(get_db)
):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    # Check if user exists
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "An account with this email already exists"
        })
    
    # Validate password
    if len(password) < 8:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Password must be at least 8 characters"
        })
    
    # Create user
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        name=name,
        company=company,
        tier="free",
        monthly_limit=10,
        notarizations_this_month=0,
        reset_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Auto-login
    token = create_access_token({"user_id": user.id, "email": user.email})
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session")
    return response


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Check if we need to reset monthly count
    if user.reset_date and datetime.utcnow() > user.reset_date:
        user.notarizations_this_month = 0
        user.reset_date = datetime.utcnow() + timedelta(days=30)
        db.commit()
    
    # Get user's data
    api_keys = db.query(APIKey).filter(APIKey.user_id == user.id, APIKey.is_active == True).all()
    recent_assets = db.query(Notarization).filter(
        Notarization.user_id == user.id
    ).order_by(Notarization.created_at.desc()).limit(10).all()
    total_assets = db.query(Notarization).filter(Notarization.user_id == user.id).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "api_keys": api_keys,
        "recent_assets": recent_assets,
        "total_assets": total_assets
    })


@router.get("/dashboard/assets", response_class=HTMLResponse)
async def dashboard_assets(request: Request, db: Session = Depends(get_db)):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    assets = db.query(Notarization).filter(
        Notarization.user_id == user.id
    ).order_by(Notarization.created_at.desc()).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "assets": assets,
        "page": "assets"
    })


# =============================================================================
# API KEYS MANAGEMENT
# =============================================================================

@router.post("/api/keys")
async def create_api_key(
    request: Request,
    name: str = Form("Default"),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    if user.tier == "free":
        return JSONResponse({"error": "Upgrade to Pro for API access"}, status_code=403)
    
    # Generate new API key
    key = APIKey(
        user_id=user.id,
        key=generate_api_key(),
        name=name
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    
    return JSONResponse({
        "message": "API key created",
        "key": key.key,
        "name": key.name
    })


@router.delete("/api/keys/{key_id}")
async def delete_api_key(
    key_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    if not key:
        return JSONResponse({"error": "Key not found"}, status_code=404)
    
    key.is_active = False
    db.commit()
    
    return JSONResponse({"message": "Key deleted"})


# =============================================================================
# PRICING PAGE
# =============================================================================

@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("pricing.html", {"request": request})


# =============================================================================
# HELPER: Validate API key for API calls
# =============================================================================

def validate_api_key(api_key: str, db: Session) -> Optional[User]:
    """Validate API key and return user if valid"""
    if not api_key or not api_key.startswith("bslt_"):
        return None
    
    key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
    if not key:
        return None
    
    # Update usage
    key.last_used = datetime.utcnow()
    key.usage_count += 1
    db.commit()
    
    return db.query(User).filter(User.id == key.user_id).first()


def check_user_limit(user: User, db: Session) -> bool:
    """Check if user can notarize (has remaining quota)"""
    # Reset if needed
    if user.reset_date and datetime.utcnow() > user.reset_date:
        user.notarizations_this_month = 0
        user.reset_date = datetime.utcnow() + timedelta(days=30)
        db.commit()
    
    return user.notarizations_this_month < user.monthly_limit


def increment_user_usage(user: User, db: Session):
    """Increment user's usage count"""
    user.notarizations_this_month += 1
    db.commit()
