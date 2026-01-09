from aiogram import BaseMiddleware
from aiogram.types import Message
from datetime import datetime
from database.db import get_user, AsyncSessionLocal
from utils.cache import is_banned, add_ban

class BanMuteMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        
        # 1. Check Memory Cache for Ban
        if is_banned(user_id):
            return # Silent ignore

        # 2. Check DB for Mute (and sync Ban if needed, though we try to keep cache updated)
        # We also need to populate cache on startup, but for safety we can check DB if not in cache?
        # The prompt optimization strategy was: Check cache, update it when action happens.
        # But if we restart, cache is empty. So we should probably check DB if we want persistence.
        # However, to strictly follow "reduce DB hits", we rely on cache.
        # Standard approach: Load bans on startup.
        
        # Check for Mute in DB (Mutes are time-based, better checked in DB or another cache)
        async with AsyncSessionLocal() as session:
            user = await get_user(session, user_id)
            if user:
                # Sync Ban to cache if found in DB but not in cache (e.g. after restart)
                if user.is_banned:
                    add_ban(user_id)
                    return # Silent ignore
                
                if user.mute_until and user.mute_until > datetime.utcnow():
                    remaining = (user.mute_until - datetime.utcnow()).seconds
                    await event.answer(f"⏳ You are muted for {remaining} seconds.")
                    return

        return await handler(event, data)
