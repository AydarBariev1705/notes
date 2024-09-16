import httpx
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.dispatcher.router import Router
from aiogram.filters import CommandStart
from bot_config import API_URL

auth_router = Router()

class AuthStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()

@auth_router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш username для входа:")
    await state.set_state(AuthStates.waiting_for_username)

@auth_router.message(AuthStates.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)
    await message.answer("Введите ваш пароль:")
    await state.set_state(AuthStates.waiting_for_password)

@auth_router.message(AuthStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    user_data = await state.get_data()
    username = user_data.get("username")
    
    if not username:
        await message.answer("Сначала введите username.")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/token", data={"username": username, "password": password})
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        await state.update_data(access_token=access_token)
        await message.answer("Вы успешно авторизованы! Введите команду для действий:\n/create_note - создать заметку\n/search_notes - поиск заметок по тегам.")
    else:
        await message.answer("Неверный username или пароль.")
    
    await state.clear()
