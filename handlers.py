from aiogram import Router, types
from tg_utils import check_subscription, check_comment
from vk_utils import check_vk_subscription
import os
import csv
from datetime import datetime

router = Router()

PARTICIPANTS_FILE = "participants.csv"
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(",")))

@router.message(lambda msg: msg.text == "/start")
async def start_handler(msg: types.Message):
    tg_check = await check_subscription(msg.from_user.id)
    comment_check = await check_comment(msg.from_user.id)
    vk_check = await check_vk_subscription(msg.from_user.username)

    if tg_check and comment_check and vk_check:
        if not is_participant(msg.from_user.id):
            with open(PARTICIPANTS_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    msg.from_user.id,
                    msg.from_user.full_name,
                    msg.from_user.username,
                    datetime.now().isoformat()
                ])
        await msg.answer("✅ Вы участвуете в розыгрыше!")
    else:
        await msg.answer("❗ Не выполнены условия.")

@router.message(lambda msg: msg.text.strip() == "!export")
async def export_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return  # молча игнорируем
    if os.path.exists(PARTICIPANTS_FILE):
        await msg.answer_document(types.FSInputFile(PARTICIPANTS_FILE))
    else:
        await msg.answer("Список участников пуст.")

def is_participant(user_id: int) -> bool:
    if not os.path.exists(PARTICIPANTS_FILE):
        return False
    with open(PARTICIPANTS_FILE, newline="") as f:
        reader = csv.reader(f)
        return any(str(user_id) == row[0] for row in reader)