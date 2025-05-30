import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
from handlers import router

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()
dp.include_router(router)

def main():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()