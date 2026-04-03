import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from .models import User
from .database import get_session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

# 1. Load the lockbox (.env file) into Python's memory
load_dotenv()

# 2. Safely grab the secret!
# If someone forgets to make a .env file, it will throw a loud error so you know immediately.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for Flask application. Did you forget your .env file?")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """Generates the JWT Wristband"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # This mathematically signs the wristband so hackers can't forge one
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials or wristband expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("user_id")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except jwt.PyJWTError: 
        raise credentials_exception
        
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
        
    return user