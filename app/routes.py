# === app/routes.py — API Routes ===

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import UserCreate, UserRead, UserUpdate, Token, Message
from app import database, models, auth
from app.db import get_db

router = APIRouter()


# === User Routes ===
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = database.get_user_by_email(user_in.email, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_password = auth.get_password_hash(user_in.password)
    new_user = models.User(email=user_in.email, password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return user


@router.put("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.password = auth.get_password_hash(user_update.password)

    db.commit()
    db.refresh(user)

    return user


# === Authentication ===
@router.post("/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    user = database.get_user_by_email(user_in.email, db)
    if not user or not auth.verify_password(user_in.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# === Health Check ===
@router.get("/health", response_model=Message)
def health_check():
    return {"detail": "EchoScript Backend is running smoothly."}
