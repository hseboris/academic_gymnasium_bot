from aiogram import Bot
import os

CHANNEL_ID = os.getenv("TELEGRAM_NUMERIC_ID")
POST_ID = int(os.getenv("TELEGRAM_POST_ID"))

bot = Bot(token=os.getenv("BOT_TOKEN"))

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

async def check_comment(user_id: int) -> bool:
    # Заглушка: Telegram API не позволяет получить все комментарии к посту
    return True