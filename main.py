import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import router

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_router(router)

def main():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()