"""Local smoke test - calls the agent directly, no WhatsApp involved."""
import database
from agent import handle_message

database.init_db()

CHAT = "972500000000@c.us"
for msg in ["היי", "באיזה שעות פתוחה המזכירות?", "הבן שלי חולה, אפשר להודיע למורה?"]:
    print(f"\n>>> משתמש: {msg}")
    reply = handle_message(CHAT, "972500000000", msg)
    print(f"<<< סביוני: {reply}")
