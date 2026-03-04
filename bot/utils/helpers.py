from telegram import Update


def parse_username(text: str) -> str | None:
    """Extract username from @mention. Returns lowercase username without @."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("@"):
        text = text[1:]
    return text.lower() if text else None


def format_inr(amount: float) -> str:
    return f"₹{amount:,.2f}"


def format_usdt(amount: float) -> str:
    return f"{amount:,.2f} USDT"


def format_both(amount_inr: float, amount_usdt: float) -> str:
    return f"{format_inr(amount_inr)} ({format_usdt(amount_usdt)})"


async def is_group_admin(update: Update) -> bool:
    """Check if the command sender is a group admin or creator."""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ("group", "supergroup"):
        member = await chat.get_member(user.id)
        return member.status in ("administrator", "creator")
    return False


def is_group_chat(update: Update) -> bool:
    return update.effective_chat.type in ("group", "supergroup")
