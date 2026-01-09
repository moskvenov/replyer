from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_admin_kb():
    kb = [
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="list:users:1")
        ],
        [
            InlineKeyboardButton(text="🚫 Те, кто в бане", callback_data="list:bans:1"),
            InlineKeyboardButton(text="🔇 Те, кто в муте", callback_data="list:mutes:1")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_action_keyboard(user_id: int, is_banned: bool = False):
    # Actions for a specific user
    # Logic: If banned -> Show Unban. If not -> Show Ban.
    
    ban_text = "✅ Разбан" if is_banned else "🚫 Бан"
    ban_callback = f"unban:{user_id}" if is_banned else f"ban:{user_id}"
    
    kb = [
        [
            InlineKeyboardButton(text=ban_text, callback_data=ban_callback),
            InlineKeyboardButton(text="🔇 Мут (время)", callback_data=f"ask_mute:{user_id}")
        ],
        [
             InlineKeyboardButton(text="🔉 Анмут", callback_data=f"unmute:{user_id}"),
             InlineKeyboardButton(text="🔙 Назад", callback_data="admin_home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
