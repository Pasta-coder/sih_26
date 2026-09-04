from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from schemas.auth import UserCreate, UserLogin, UserOut, Token
from auth_utils import hash_password, verify_password, create_access_token, get_current_user, require_admin

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin-only account creation. Only the 'officer' role may be created here."""
    # SECURITY (S1): This endpoint is gated behind require_admin, so anonymous
    # users can no longer self-register. Additionally, the client-supplied role
    # is validated server-side: anything other than 'officer' (e.g. 'admin') is
    # rejected, so no caller can mint privileged accounts through the public API.
    if payload.role != UserRole.officer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the officer role can be created via /register. "
                   "Admin accounts are provisioned by an administrator.",
        )
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,  # guaranteed to be UserRole.officer by the check above
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
