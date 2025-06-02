from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import os
import csv
import json
from datetime import datetime
from random import sample, shuffle
from asyncio import sleep

from tg_utils import check_subscription
from vk_utils import resolve_vk_id, check_vk_subscription

load_dotenv()
router = Router()

PARTICIPANTS_FILE = "participants.csv"
LINK_FILE = "vk_links.json"
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(",")))
VK_GROUP_URL = os.getenv("VK_GROUP_URL")
TELEGRAM_LINK = os.getenv("TELEGRAM_LINK")


class VKInput(StatesGroup):
    waiting_for_vk_username = State()

class DrawState(StatesGroup):
    waiting_for_prize_count = State()


def save_vk_link(tg_id, vk_id):
    data = {}
    if os.path.exists(LINK_FILE):
        with open(LINK_FILE, "r") as f:
            data = json.load(f)
    data[str(tg_id)] = vk_id
    with open(LINK_FILE, "w") as f:
        json.dump(data, f)


def get_vk_link(tg_id):
    if not os.path.exists(LINK_FILE):
        return None
    with open(LINK_FILE, "r") as f:
        data = json.load(f)
    return data.get(str(tg_id))


def is_participant(user_id: int) -> bool:
    if not os.path.exists(PARTICIPANTS_FILE):
        return False
    with open(PARTICIPANTS_FILE, newline="") as f:
        return any(str(user_id) == row[0] for row in csv.reader(f))


@router.message(lambda msg: msg.text == "/start")
async def handle_start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Принять участие", callback_data="participate")]
    ])
    await msg.answer("Добро пожаловать! Чтобы принять участие в розыгрыше, нажмите кнопку ниже:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "participate")
async def handle_participation(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if is_participant(user_id):
        await callback.message.answer("✅ Вы уже участвуете в розыгрыше!")
        return

    await callback.message.answer("✍️ Пожалуйста, введите ваш VK username (например, @durov или durov):")
    await state.set_state(VKInput.waiting_for_vk_username)


@router.message(VKInput.waiting_for_vk_username)
async def process_vk_username(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    username = msg.from_user.username
    full_name = msg.from_user.full_name

    vk_username = msg.text.strip()
    vk_id = resolve_vk_id(vk_username)
    if vk_id is None:
        await msg.answer("❌ Не удалось найти пользователя с таким username. Попробуйте ещё раз.")
        return

    save_vk_link(user_id, vk_id)

    tg_check = await check_subscription(user_id)
    vk_check = check_vk_subscription(vk_id)

    errors = []
    if not tg_check:
        errors.append(f"❌ Нет подписки на Telegram-канал: <a href='{TELEGRAM_LINK}'>перейти</a>")
    if not vk_check:
        errors.append(f"❌ Нет подписки на группу ВКонтакте: <a href='{VK_GROUP_URL}'>перейти</a>")

    if not errors:
        with open(PARTICIPANTS_FILE, "a", newline="") as f:
            csv.writer(f).writerow([
                user_id,
                full_name,
                username,
                datetime.now().isoformat()
            ])
        await msg.answer("✅ Вы участвуете в розыгрыше! 🎉")
    else:
        await msg.answer("🚫 Условия не выполнены:\n" + "\n".join(errors), parse_mode="HTML")

    await state.clear()


@router.message(lambda msg: msg.text == "/list" and msg.from_user.id in ADMIN_IDS)
async def list_participants(msg: types.Message):
    if not os.path.exists(PARTICIPANTS_FILE):
        await msg.answer("📭 Пока никто не зарегистрировался.")
        return

    with open(PARTICIPANTS_FILE, newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        await msg.answer("📭 Пока никто не зарегистрировался.")
        return

    text = "📋 Список участников:\n\n"
    for i, row in enumerate(rows, 1):
        tg_id, full_name, username, dt = row
        line = f"{i}. {full_name} ({username or 'без username'}), ID: {tg_id}\n"
        if len(text + line) > 4000:
            await msg.answer(text)
            text = ""
        text += line

    if text:
        await msg.answer(text)


@router.message(lambda msg: msg.text == "/draw" and msg.from_user.id in ADMIN_IDS)
async def start_draw(msg: types.Message, state: FSMContext):
    await msg.answer("🎰 Сколько призов разыграть?")
    await state.set_state(DrawState.waiting_for_prize_count)


@router.message(DrawState.waiting_for_prize_count)
async def process_draw(msg: types.Message, state: FSMContext):
    try:
        n = int(msg.text.strip())
        if n <= 0:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Введите положительное число.")
        return

    if not os.path.exists(PARTICIPANTS_FILE):
        await msg.answer("📭 Нет зарегистрированных участников.")
        await state.clear()
        return

    with open(PARTICIPANTS_FILE, newline="") as f:
        rows = list(csv.reader(f))

    eligible = []
    for row in rows:
        tg_id, full_name, username, _ = row
        vk_id = get_vk_link(int(tg_id))
        if not vk_id:
            continue
        tg_ok = await check_subscription(int(tg_id))
        vk_ok = check_vk_subscription(vk_id)
        if tg_ok and vk_ok:
            eligible.append((tg_id, full_name, username))

    if len(eligible) < n:
        await msg.answer(f"❗ Недостаточно участников, прошедших проверку. Только {len(eligible)}.")
        await state.clear()
        return

    winners = sample(eligible, n)
    shuffle(winners)

    await msg.answer(f"🎉 Победителей будет: {n}\nЗапускаем розыгрыш...")
    await sleep(1)

    for i, (tg_id, name, username) in enumerate(winners, 1):
        await msg.answer(
            f"🏆 Победитель #{i}: <b>{name}</b> ({username or 'без username'}) — <a href='tg://user?id={tg_id}'>связаться</a>",
            parse_mode="HTML"
        )
        await sleep(1.5)

    await state.clear()