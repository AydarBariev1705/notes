import httpx
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from bot_config import API_URL


# Инициализация роутера
notes_router = Router()

class NoteStates(StatesGroup):
    waiting_for_note_title = State()
    waiting_for_note_content = State()
    waiting_for_note_tags = State()
    waiting_for_search_tag = State()

@notes_router.message(Command(commands=['create_note']))
async def create_note_start(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    token = user_data.get("access_token")
    if not token:
        await message.answer("Сначала авторизуйтесь.")
        return
    
    await message.answer("Введите заголовок заметки:")
    await state.set_state(NoteStates.waiting_for_note_title)

@notes_router.message(NoteStates.waiting_for_note_title)
async def process_note_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите содержимое заметки:")
    await state.set_state(NoteStates.waiting_for_note_content)

@notes_router.message(NoteStates.waiting_for_note_content)
async def process_note_content(message: types.Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.answer("Введите теги заметки (через запятую):")
    await state.set_state(NoteStates.waiting_for_note_tags)

@notes_router.message(NoteStates.waiting_for_note_tags)
async def process_note_tags(message: types.Message, state: FSMContext):
    tags = message.text.split(',')
    data = await state.get_data()
    note_data = {
        "title": data["title"],
        "content": data["content"],
        "tags": [tag.strip() for tag in tags]
    }
    
    token = data.get("access_token")
    if token is None:
        await message.answer("Сначала авторизуйтесь.")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/notes/create", json=note_data, headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code == 200:
        await message.answer("Заметка успешно создана!")
    else:
        await message.answer("Ошибка создания заметки.")
    
    await state.clear()

@notes_router.message(Command(commands=['search_notes']))
async def search_notes_start(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    token = user_data.get("access_token")
    if not token:
        await message.answer("Сначала авторизуйтесь.")
        return
    
    await message.answer("Введите тег для поиска заметок:")
    await state.set_state(NoteStates.waiting_for_search_tag)

@notes_router.message(NoteStates.waiting_for_search_tag)
async def process_search_tag(message: types.Message, state: FSMContext):
    tag = message.text
    user_data = await state.get_data()
    token = user_data.get("access_token")
    
    if token is None:
        await message.answer("Сначала авторизуйтесь.")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/notes/search", params={"tag": tag}, headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code == 200:
        notes = response.json()
        if notes:
            notes_message = "\n".join([f"Note {note['id']}: {note['title']} - {note['content']}" for note in notes])
        else:
            notes_message = "Нет заметок с таким тегом."
        await message.answer(notes_message)
    else:
        await message.answer("Ошибка поиска заметок.")
    
    await state.clear()
