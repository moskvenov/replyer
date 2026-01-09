import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import add_user, AsyncSessionLocal
from config import ADMIN_IDS

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    async with AsyncSessionLocal() as session:
        await add_user(session, user_id=user.id, first_name=user.first_name, username=user.username)
    
    await message.answer(
        f"👋 Привет, {user.first_name}!\n"
        "Отправь мне сообщение с твоим предложением или вопросом, и я передам его администраторам."
    )

@router.message()
async def handle_feedback(message: Message, bot):
    # Depending on middleware order, throttling/ban checks happened before this.
    
    user = message.from_user
    
    # Check if user is admin
    if user.id in ADMIN_IDS:
        # Admins cannot use bot for feedback
        # Silent ignore to prevent recursion and allow Mute FSM to work without "You can't send messages" error
        return

    # Format message for admin:
    # We include ID so we can parse it for reply implementation.
    # Format: "#id123456789\nName: ...\nMessage: ..."
    
    # Format:
    # 📩 <id> (code)
    # Никнейм (@user)
    # 
    # Message...
    
    # Using HTML/MarkdownV2 logic? Let's use simple formatting.
    # User requested: "смайлик конвертика <id> (форматированый, можно скопировать)\nНикнейм (@username)\n\n само сообщение"
    
    # We strip # from ID to make it just the number for copy
    info_header = (
        f"📩 `{user.id}`\n"
        f"{user.full_name} (@{user.username or 'NoUser'})\n"
    )
    
    admin_received = False
    for admin_id in ADMIN_IDS:
        try:
            # We add double newline before text
            if message.text:
                await bot.send_message(admin_id, f"{info_header}\n{message.text}", parse_mode="Markdown")
            elif message.photo or message.video or message.document or message.voice or message.audio:
                # Copy media with caption
                caption = f"{info_header}\n{message.caption or ''}"
                await message.copy_to(admin_id, caption=caption, parse_mode="Markdown")
            else:
                 await bot.send_message(admin_id, f"{info_header}\n[Неподдерживаемый тип медиа]", parse_mode="Markdown")
            admin_received = True
        except Exception as e:
            # Log error
            print(f"FAILED TO SEND TO ADMIN {admin_id}: {e}")
            pass

    if admin_received:
        # Ephemeral Success Message
        sent_msg = await message.answer("✅ Сообщение успешно отправлено!")
        # Removed message.react to avoid REACTION_INVALID checks failure
        await asyncio.sleep(3)
        try:
            await sent_msg.delete()
        except:
            pass
