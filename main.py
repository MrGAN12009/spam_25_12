import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
from aiogram import F

API_TOKEN = "6852263140:AAH47rcJm47MDnK6T4lYxd8N-jGWfGDBwQo"  # Замените на ваш токен

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключение к базе данных
db = sqlite3.connect("users.db")
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY
)
""")
db.commit()

# Клавиатура для управления
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/spam")],
    ],
    resize_keyboard=True
)

# Определение состояний для FSM
class SpamStates(StatesGroup):
    waiting_for_message = State()

# Хендлер для команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    db.commit()
    await message.answer("Привет! Ты добавлен в базу данных.", reply_markup=keyboard)

# Хендлер для команды /spam
@dp.message(Command("spam"))
async def spam_command(message: types.Message, state: FSMContext):
    await message.answer("Отправьте сообщение (текст, фото, файл и т.д.) для рассылки.")
    await state.set_state(SpamStates.waiting_for_message)

# Хендлер для получения сообщения в состоянии ожидания рассылки
@dp.message(SpamStates.waiting_for_message, F.content_type.in_({"text", "photo", "document", "audio", "video"}))
async def broadcast(message: types.Message, state: FSMContext):
    # Определяем тип контента
    if message.photo:
        photo = message.photo[-1].file_id
        caption = message.caption
        content_type = "photo"
    elif message.document:
        document = message.document.file_id
        caption = message.caption
        content_type = "document"
    elif message.audio:
        audio = message.audio.file_id
        caption = message.caption
        content_type = "audio"
    elif message.video:
        video = message.video.file_id
        caption = message.caption
        content_type = "video"
    else:
        text = message.text
        content_type = "text"

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    successful = 0
    for user in users:
        try:
            if content_type == "photo":
                await bot.send_photo(chat_id=user[0], photo=photo, caption=caption)
            elif content_type == "document":
                await bot.send_document(chat_id=user[0], document=document, caption=caption)
            elif content_type == "audio":
                await bot.send_audio(chat_id=user[0], audio=audio, caption=caption)
            elif content_type == "video":
                await bot.send_video(chat_id=user[0], video=video, caption=caption)
            elif content_type == "text":
                await bot.send_message(chat_id=user[0], text=text)
            successful += 1
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user[0]}: {e}")

    await message.answer(f"Рассылка завершена. Успешно отправлено: {successful}.")
    await state.clear()  # Сбрасываем состояние

# Игнорирование других сообщений, если состояние не активно
@dp.message()
async def ignore_message(message: types.Message):
    await message.answer("Используйте команду /spam, чтобы начать рассылку.")

# Основная функция
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
