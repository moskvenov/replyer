# Simple in-memory storage for banned users to avoid circular imports and DB hits
# This set should be populated on startup and updated on ban/unban

BANNED_USERS = set()

def is_banned(user_id: int) -> bool:
    return user_id in BANNED_USERS

def add_ban(user_id: int):
    BANNED_USERS.add(user_id)

def remove_ban(user_id: int):
    BANNED_USERS.discard(user_id)
