from aiogram.utils.markdown import hbold, hlink

def format_user_link(user_id: int, first_name: str) -> str:
    return hlink(first_name, f"tg://user?id={user_id}")
