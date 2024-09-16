from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
from app.crud import create_note, update_note_tags, get_notes, get_note_by_id, delete_note, create_user, get_user_by_username, update_note, search_notes_by_tag
from app.schemas import NoteCreate, NoteInDB, NoteUpdate, UserCreate, Token, User
from app.database import get_db
from app.auth import get_current_user, oauth2_scheme, create_access_token, verify_password
from app.app_config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/api",
    tags=["notes"],
)

# Маршруты для заметок
@router.post("/notes/", response_model=NoteInDB)
async def create_note_endpoint(note: NoteCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    db_note = create_note(db, note, user.id)
    update_note_tags(db, db_note, set(note.tags))
    return db_note

@router.get("/notes/", response_model=List[NoteInDB])
async def read_notes_endpoint(skip: int = 0, limit: int = 10, tag: Optional[str] = None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    notes = get_notes(db, user.id, skip, limit, tag)
    if notes is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    return notes

@router.get("/notes/{note_id}", response_model=NoteInDB)
async def read_note_endpoint(note_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    note = get_note_by_id(db, note_id, user.id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    return note

@router.put("/notes/{note_id}", response_model=NoteInDB)
async def update_note_endpoint(note_id: int, note_update: NoteUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    db_note = get_note_by_id(db, note_id, user.id)
    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    db_note = update_note(db, db_note, note_update)
    update_note_tags(db, db_note, set(note_update.tags))
    return db_note

@router.delete("/notes/{note_id}", response_model=NoteInDB)
async def delete_note_endpoint(note_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    db_note = get_note_by_id(db, note_id, user.id)
    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    delete_note(db, db_note)
    return db_note

# Маршруты для пользователей и аутентификации
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=User)
async def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.get("/notes/search")
async def search_notes(tag: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notes = search_notes_by_tag(db, current_user.id, tag)
    if not notes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No notes found for the given tag")
    return notes