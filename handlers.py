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
    user_id = msg.from_user.id
    username = msg.from_user.username

    tg_check = await check_subscription(user_id)
    comment_check = await check_comment(user_id)
    vk_check = check_vk_subscription(username)

    errors = []
    if not tg_check:
        errors.append("❌ Нет подписки на Telegram-канал")
    if not comment_check:
        errors.append("❌ Нет комментария под постом")
    if not vk_check:
        errors.append("❌ Нет подписки на группу ВКонтакте")

    if not errors:
        if not is_participant(user_id):
            with open(PARTICIPANTS_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    user_id,
                    msg.from_user.full_name,
                    username,
                    datetime.now().isoformat()
                ])
        await msg.answer("✅ Вы участвуете в розыгрыше!")
    else:
        await msg.answer("🚫 Условия не выполнены:\n" + "\n".join(errors))

@router.message(lambda msg: msg.text.strip() == "!export")
async def export_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    if os.path.exists(PARTICIPANTS_FILE):
        await msg.answer_document(types.FSInputFile(PARTICIPANTS_FILE))
    else:
        await msg.answer("Список участников пуст.")

@router.message(lambda msg: msg.text.strip() == "!audit")
async def audit_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    if not os.path.exists(PARTICIPANTS_FILE):
        await msg.answer("Файл участников не найден.")
        return

    results = []
    with open(PARTICIPANTS_FILE, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            uid, name, username, _ = row
            uid = int(uid)
            tg_ok = await check_subscription(uid)
            vk_ok = check_vk_subscription(username)
            status = []
            if tg_ok and vk_ok:
                results.append(f"✅ {name} (@{username})")
            else:
                if not tg_ok:
                    status.append("TG ❌")
                if not vk_ok:
                    status.append("VK ❌")
                results.append(f"❌ {name} (@{username}) — {', '.join(status)}")

    await msg.answer("📋 Аудит участников:\n" + "\n".join(results))

def is_participant(user_id: int) -> bool:
    if not os.path.exists(PARTICIPANTS_FILE):
        return False
    with open(PARTICIPANTS_FILE, newline="") as f:
        reader = csv.reader(f)
        return any(str(user_id) == row[0] for row in reader)