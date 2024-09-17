from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status 
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models import User
from app.app_config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(
    schemes=["bcrypt"],
      deprecated="auto",
      )
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(
        plain_password: str,
        hashed_password: str,
          ) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
        ) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY, 
        algorithm=ALGORITHM,
        )
    return encoded_jwt



def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
        ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = db.execute(select(User).filter(User.username == username)).scalars().first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user


