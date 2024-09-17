import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
from app.crud import (create_note, 
                      update_note_tags, 
                      get_notes, 
                      get_note_by_id, 
                      delete_note, 
                      create_user, 
                      get_user_by_username, 
                      update_note, 
                      search_notes_by_tag)
from app.schemas import (NoteCreate, 
                         NoteInDB, 
                         NoteUpdate, 
                         UserCreate, 
                         Token, 
                         User)
from app.database import get_db
from app.auth import (get_current_user, 
                      oauth2_scheme, 
                      create_access_token, 
                      verify_password)
from app.app_config import ACCESS_TOKEN_EXPIRE_MINUTES

# Настройка логирования
logger = logging.getLogger("notes_api")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("logs/notes_api.log", when="midnight", interval=1, backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter(
    tags=["notes"],
)

@router.post(
        "/notes/", 
        response_model=NoteInDB,
        )
async def create_note_endpoint(
    note: NoteCreate, 
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme),
    ):
    user = get_current_user(
        token=token, 
        db=db,
        )
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            )
    
    db_note = create_note(
        db=db, 
        note=note, 
        user_id=user.id,
        )
    update_note_tags(
        db=db, 
        db_note=db_note, 
        new_tags=set(note.tags),
        )
    logger.info(f"Note created successfully: {db_note.id}")
    return db_note

@router.get(
        "/notes/", 
        response_model=List[NoteInDB],
        )
async def read_notes_endpoint(
    tag: Optional[str] = None, 
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme),
    ):
    user = get_current_user(
        token=token, 
        db=db,
        )
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            )
    
    notes = get_notes(
        db=db, 
        user_id=user.id, 
        tag=tag,
        )
    if notes is None:
        logger.info("Tag not found: %s", tag)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Tag not found",
            )
    
    logger.info(f"Notes retrieved: {len(notes)} notes found")
    return notes

@router.get(
        "/notes/{note_id}", 
        response_model=NoteInDB,
        )
async def read_note_endpoint(
    note_id: int, 
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme),
    ):
    user = get_current_user(
        token=token, 
        db=db,
        )
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            )
    
    note = get_note_by_id(
        db=db, 
        note_id=note_id, 
        user_id=user.id,
        )
    if not note:
        logger.info(f"Note not found: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Note not found",
            )
    
    logger.info(f"Note retrieved: {note_id}")
    return note

@router.put(
        "/notes/{note_id}", 
        response_model=NoteInDB,
        )
async def update_note_endpoint(
    note_id: int, 
    note_update: NoteUpdate, 
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme),
    ):
    user = get_current_user(
        token=token, 
        db=db,
        )
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            )

    db_note = get_note_by_id(
        db=db, 
        note_id=note_id, 
        user_id=user.id,
        )
    if not db_note:
        logger.info(f"Note not found: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Note not found",
            )

    db_note = update_note(
        db=db, 
        db_note=db_note, 
        note_update=note_update,
        )
    update_note_tags(
        db=db, 
        db_note=db_note, 
        new_tags=set(note_update.tags),
        )
    logger.info(f"Note updated: {note_id}")
    return db_note

@router.delete("/notes/{note_id}")
async def delete_note_endpoint(
    note_id: int, 
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme),
    ):
    user = get_current_user(
        token=token, 
        db=db,
        )
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            )

    db_note = get_note_by_id(
        db=db, 
        note_id=note_id, 
        user_id=user.id,
        )
    if not db_note:
        logger.info(f"Note not found: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Note not found",
            )

    delete_note(
        db=db,
        db_note=db_note,
        )
    logger.info(f"Note deleted: {note_id}")
    return {"message": f"Note id:{note_id} deleted successfully"}

@router.post(
        "/token", 
        response_model=Token,
        )
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    ):
    user = get_user_by_username(
        db=db, 
        username=form_data.username,
        )
    if not user or not verify_password(
        plain_password=form_data.password, 
        hashed_password=user.hashed_password,
        ):
        logger.warning("Invalid credentials for user: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password", 
            headers={"WWW-Authenticate": "Bearer"},
            )
    
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires,
        )
    logger.info(f"User logged in: {form_data.username}")
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        }

@router.post(
        "/users/", 
        response_model=User,
        )
async def create_user_endpoint(
    user: UserCreate, 
    db: Session = Depends(get_db),
    ):
    created_user = create_user(
        db=db, 
        user=user,
        )
    logger.info(f"User created: {created_user.username}")
    return created_user


@router.get("/search")
async def search_notes(
    tag: str, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db),
    ):
    user = get_current_user(
        token=token, 
        db=db,
        )
    if not user:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials",
            )
    notes = search_notes_by_tag(
        db=db, 
        user_id=user.id, 
        tag=tag,
        )
    if not notes:
        logger.info(f"No notes found for tag: {tag}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No notes found for the given tag",
            )
    logger.info(f"Notes found for tag: {tag}")
    return notes
