import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F


API_TOKEN = "6852263140:AAH47rcJm47MDnK6T4lYxd8N-jGWfGDBwQo"  # Замените на ваш токен


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


db = sqlite3.connect("users.db")
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY
)
""")
db.commit()


keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Рассылка")]
    ],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    db.commit()
    await message.answer("Привет! Ты добавлен в базу данных.", reply_markup=keyboard)


@dp.message(lambda msg: msg.text == "Рассылка")
async def broadcast_prompt(message: types.Message):
    await message.answer("Отправьте текст или фото с подписью для рассылки.")


from aiogram import F

@dp.message(F.content_type.in_({"text", "photo", "document", "audio", "video"}))
async def broadcast(message: types.Message):
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


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
