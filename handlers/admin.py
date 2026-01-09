import re
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.db import (
    AsyncSessionLocal, User, get_user, 
    get_all_users_count, get_banned_users_count, get_muted_users_count,
    get_users_paginated, get_banned_paginated, get_muted_paginated,
    get_new_users_period
)
from utils.admin_utils import IsAdmin
from utils.time_utils import format_dt
from utils.cache import add_ban, remove_ban
from keyboards.admin_kb import get_action_keyboard, main_admin_kb
from keyboards.pagination import create_pagination_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

class AdminStates(StatesGroup):
    waiting_for_mute_time = State()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    await message.answer("🔧 **Панель Администратора**", reply_markup=main_admin_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_home")
async def admin_home_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🔧 **Панель Администратора**", reply_markup=main_admin_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        total = await get_all_users_count(session)
        banned = await get_banned_users_count(session)
        muted = await get_muted_users_count(session)
        new24h = await get_new_users_period(session, timedelta(hours=24))
        new7d = await get_new_users_period(session, timedelta(days=7))
    
    text = (
        f"📊 **Подробная Статистика**\n\n"
        f"👥 Всего пользователей: `{total}`\n"
        f"🔥 Новых за 24 часа: `{new24h}`\n"
        f"📅 Новых за 7 дней: `{new7d}`\n"
        f"🚫 Забанено: `{banned}`\n"
        f"🔇 В муте: `{muted}`\n"
    )
    # Add back button
    await callback.message.edit_text(text, reply_markup=main_admin_kb(), parse_mode="Markdown")

# --- LISTS HANDLERS ---
@router.callback_query(F.data.startswith("list:"))
async def show_list(callback: CallbackQuery):
    # data: list:type:page
    parts = callback.data.split(":")
    list_type = parts[1]
    page = int(parts[2])
    limit = 10
    
    async with AsyncSessionLocal() as session:
        if list_type == "users":
            items = await get_users_paginated(session, page, limit)
            total = await get_all_users_count(session)
            label = "Пользователи"
        elif list_type == "bans":
            items = await get_banned_paginated(session, page, limit)
            total = await get_banned_users_count(session)
            label = "Бан-лист"
        elif list_type == "mutes":
            items = await get_muted_paginated(session, page, limit)
            total = await get_muted_users_count(session)
            label = "Мут-лист"
        else:
            return await callback.answer("Error")
            
    if not items and page == 1:
        text = f"📂 **{label}**: Пусто"
        # still show menu
        kb = main_admin_kb() # Fallback to main menu if empty? Or show empty list logic?
        # Let's show "Empty" message but with Back button
        # Actually create pagination with empty list works if total=0?
        if total == 0:
             await callback.message.edit_text(f"📂 **{label}**: Список пуст", reply_markup=main_admin_kb(), parse_mode="Markdown")
             return
            
    text = f"📂 **{label}** (Стр. {page})"
    kb = create_pagination_keyboard(
        items=items,
        page=page,
        total_count=total,
        items_per_page=limit,
        callback_prefix=f"list:{list_type}",
        item_key="user_id",
        item_label="first_name"
    )
        
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery):
    await callback.answer()

# --- INFO & ACTIONS ---

@router.message(Command("info"))
async def user_info_cmd(message: Message):
    # Usage: /info 123456
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Использование: /info <user_id>")
    
    user_id_str = args[1]
    if not user_id_str.isdigit():
        return await message.answer("Неверный ID")
        
    await show_user_info(message, int(user_id_str))

@router.callback_query(F.data.startswith("info:"))
async def user_info_cb(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    await show_user_info(callback.message, user_id, is_edit=True)

async def show_user_info(event: Message, user_id: int, is_edit: bool = False):
    async with AsyncSessionLocal() as session:
        user = await get_user(session, user_id)
        if not user:
            msg = "Пользователь не найден в БД."
            if is_edit: await event.edit_text(msg, reply_markup=main_admin_kb())
            else: await event.answer(msg)
            return
        
        status = "✅ Активен"
        if user.is_banned:
            status = "🚫 ЗАБАНЕН"
        elif user.mute_until and user.mute_until > datetime.utcnow():
            status = f"🔇 В МУТЕ до {format_dt(user.mute_until)}"
            
        text = (
            f"👤 **Профиль пользователя**\n"
            f"🆔 ID: `{user.user_id}`\n"
            f"👤 Имя: {user.first_name}\n"
            f"🔗 Username: @{user.username or 'Нет'}\n"
            f"📅 Дата регистрации: {format_dt(user.joined_at)}\n"
            f"📊 Статус: {status}"
        )
        
        kb = get_action_keyboard(user_id, is_banned=user.is_banned)
        
        if is_edit:
            await event.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await event.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- ACTION LOGIC ---

@router.callback_query(F.data.startswith("ban:"))
async def ban_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        user = await get_user(session, user_id)
        if user:
            user.is_banned = True
            await session.commit()
            add_ban(user_id) 
            await callback.answer("Пользователь забанен.")
            # Force delay or ensure logic? Database commit is awaited.
            # We call show_user_info to refresh the view.
            await show_user_info(callback.message, user_id, is_edit=True)

@router.callback_query(F.data.startswith("unban:"))
async def unban_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        user = await get_user(session, user_id)
        if user:
            user.is_banned = False
            await session.commit()
            remove_ban(user_id)
            await callback.answer("Пользователь разбанен.")
            await show_user_info(callback.message, user_id, is_edit=True)

# MUTE FSM
@router.callback_query(F.data.startswith("ask_mute:"))
async def ask_mute_user(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminStates.waiting_for_mute_time)
    await callback.message.answer(f"⏳ Введите время мута в минутах для пользователя {user_id}:")
    await callback.answer()

@router.message(AdminStates.waiting_for_mute_time)
async def process_mute_time(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число (минуты).")
        return
    
    minutes = int(message.text)
    data = await state.get_data()
    user_id = data.get("target_user_id")
    
    async with AsyncSessionLocal() as session:
        user = await get_user(session, user_id)
        if user:
            user.mute_until = datetime.utcnow() + timedelta(minutes=minutes)
            await session.commit()
            await message.answer(f"✅ Пользователь {user_id} замучен на {minutes} минут.")
    
    await state.clear()
    # Optionally show updated info
    await show_user_info(message, user_id)

@router.callback_query(F.data.startswith("unmute:"))
async def unmute_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        user = await get_user(session, user_id)
        if user:
            user.mute_until = None
            await session.commit()
            await callback.answer("Пользователь размучен")
            await show_user_info(callback.message, user_id, is_edit=True)

# Reply System in Admin
@router.message(F.reply_to_message)
async def reply_to_user(message: Message, bot):
    # Check if admin is replying to a forwarded message OR a bot message with #id tag
    replied_msg = message.reply_to_message
    
    target_user_id = None
    
    # Check text for ID tag (User format: "📩 123456789")
    text_to_check = replied_msg.text or replied_msg.caption or ""
    # Regex robust to plain text (no backticks needed in pattern if text attribute strips them)
    # We look for envelope + digits
    match = re.search(r"📩\s*(\d+)", text_to_check)
    if match:
        target_user_id = int(match.group(1))
    
    if target_user_id:
        try:
            # Users must see just message from bot (no "Reply from support" header)
            await bot.send_message(target_user_id, message.text)
            await message.reply("✅ Ответ отправлен.")
        except Exception as e:
            await message.answer(f"Ошибка отправки: {e}")
    else:
        # Maybe just a normal reply between admins? Ignore.
        pass
