import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def ledger_pagination_keyboard(current_page: int, total_pages: int,
                               user_a_id: int, user_b_id: int, group_id: int) -> InlineKeyboardMarkup | None:
    if total_pages <= 1:
        return None

    buttons = []
    # callback data format: ledger:{group_id}:{user_a}:{user_b}:{page}
    if current_page > 1:
        buttons.append(InlineKeyboardButton(
            "⬅ Prev",
            callback_data=f"ledger:{group_id}:{user_a_id}:{user_b_id}:{current_page - 1}",
        ))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(
            "Next ➡",
            callback_data=f"ledger:{group_id}:{user_a_id}:{user_b_id}:{current_page + 1}",
        ))

    return InlineKeyboardMarkup([buttons]) if buttons else None
