from sqlalchemy.orm import Session
from sqlalchemy.future import select

from app.models import User, Note, Tag
from app.schemas import UserCreate, NoteCreate, NoteUpdate
from app.auth import get_password_hash


def get_user_by_username(
        db: Session, 
        username: str,
        ):
    return db.execute(select(User).filter(User.username == username)).scalars().first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_note(
        db: Session, 
        note: NoteCreate, 
        user_id: int,
        ):
    db_note = Note(
        title=note.title, 
        content=note.content, 
        user_id=user_id,
        )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def get_notes(
        db: Session, 
        user_id: int, 
        tag: str = None,
        ):
    query = db.execute(select(Note).filter(Note.user_id == user_id))
    if tag:
        tag_obj = db.execute(select(Tag).filter(Tag.name == tag)).scalars().first()
        if not tag_obj:
            return None
        query = db.execute(select(Note).join(Note.tags).filter(Tag.id == tag_obj.id).filter(Note.user_id == user_id))
    return query.scalars().all()

def get_note_by_id(
        db: Session, 
        note_id: int, 
        user_id: int,
        ):
    return db.execute(select(Note).filter(Note.id == note_id, Note.user_id == user_id)).scalars().first()

def update_note(
        db: Session, 
        db_note: Note, 
        note_update: NoteUpdate,
        ):
    db_note.title = note_update.title
    db_note.content = note_update.content
    return db_note

def delete_note(db: Session, db_note: Note):
    db.delete(db_note)
    db.commit()

# Работа с тегами
def get_tag_by_name(
        db: Session, 
        tag_name: str,
        ):
    return db.execute(select(Tag).filter(Tag.name == tag_name)).scalars().first()

def create_tag(
        db: Session, 
        tag_name: str,
        ):
    tag = Tag(name=tag_name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

def update_note_tags(
        db: Session, 
        db_note: Note, 
        new_tags: set,
        ):
    existing_tags = {tag.name for tag in db_note.tags}
    tags_to_add = new_tags - existing_tags
    tags_to_remove = existing_tags - new_tags

    for tag_name in tags_to_remove:
        tag = get_tag_by_name(db, tag_name)
        if tag:
            db_note.tags.remove(tag)

    for tag_name in tags_to_add:
        tag = get_tag_by_name(db, tag_name)
        if not tag:
            tag = create_tag(db, tag_name)
        db_note.tags.append(tag)

    db.commit()
    db.refresh(db_note)
    return db_note

def search_notes_by_tag(
        db: Session, 
        user_id: int, 
        tag: str,
        ):
    return db.execute(
        select(Note).join(Note.tags).filter(
            Note.user_id == user_id,
            Tag.name == tag,
            )
    ).scalars().all()
