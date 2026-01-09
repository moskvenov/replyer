from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def create_pagination_keyboard(
    items: list, # List of dicts or objects. If objects, ensure we can extract ID/Text
    page: int,
    total_count: int,
    items_per_page: int,
    callback_prefix: str,
    item_key: str = "user_id", # Attribute to use for callback ID
    item_label: str = "first_name" # Attribute to use for button text
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Items are already paginated from DB usually, but if 'items' is the full list:
    # We assume 'items' passed here is JUST the page's items.
    
    for item in items:
        # Support both dict and object access
        if isinstance(item, dict):
            text = item.get(item_label, "Unknown")
            data_id = item.get(item_key, 0)
        else:
            text = getattr(item, item_label, "Unknown")
            data_id = getattr(item, item_key, 0)
            
        # 1 column layout requested: "1 user - 1 row"
        builder.row(InlineKeyboardButton(text=f"{text[:30]} ({data_id})", callback_data=f"info:{data_id}")) # Go to info directly
        
    # Navigation
    # Format: [ < ] [ 2/30 ] [ > ]
    
    # Calculate max pages (avoid division by zero if total_count is 0, though items check handles empty list)
    max_page = (total_count + items_per_page - 1) // items_per_page
    if max_page < 1: max_page = 1
    
    nav_row = []
    
    # Back Arrow
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{callback_prefix}:{page-1}"))
    else:
         # Placeholder to keep alignment if desired, or just omit. Omit is cleaner.
         pass

    # Page Counter
    nav_row.append(InlineKeyboardButton(text=f"{page}/{max_page}", callback_data="noop"))
    
    # Forward Arrow
    if page < max_page:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"{callback_prefix}:{page+1}"))
        
    builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_home"))
    
    return builder.as_markup()
