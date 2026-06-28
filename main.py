import logging, os, random, sqlite3
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (Application, CommandHandler, MessageHandler, 
                          ChatMemberHandler, filters, ContextTypes)

# --- Keep Alive ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "မြနှင်း Bot Online ❤️"
Thread(target=lambda: app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()

# --- Config ---
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 7771663458
CHANNEL_ID = -1003841480184
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS users (chat_id INTEGER, user_id INTEGER, username TEXT, gender TEXT)")
db.commit()

# --- Helpers ---
async def get_user_info(u):
    user = u.effective_user
    mention = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
    return f"👤 Name: {user.full_name}\n🆔 ID: `{user.id}`\n🔗 Username: {mention}"

# --- Systems ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.type in ["group", "supergroup"]:
        cur.execute("INSERT OR IGNORE INTO groups VALUES (?)", (u.effective_chat.id,))
        db.commit()
    keyboard = [[InlineKeyboardButton("📢 Channel", url="https://t.me/BOTUAPTE")],
                [InlineKeyboardButton("🫅 Owner @Tear808", url="https://t.me/Tear808")]]
    await u.message.reply_text("🎀 မြနှင်း ရောက်ရှိပါပြီရှင့်! 😘", reply_markup=InlineKeyboardMarkup(keyboard))

async def teach(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if c.args and u.message.reply_to_message:
        cur.execute("REPLACE INTO memory VALUES (?, ?)", (c.args[0].lower(), u.message.reply_to_message.text))
        db.commit()
        await u.message.reply_text("✅ မှတ်သားလိုက်ပြီနော်။")

async def forward_and_others(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # Channel Forwarding
    if u.channel_post and u.channel_post.chat.id == CHANNEL_ID:
        cur.execute("SELECT chat_id FROM groups")
        for (gid,) in cur.fetchall():
            try: await c.bot.forward_message(gid, CHANNEL_ID, u.channel_post.message_id)
            except: continue
    
    # Owner Forwarding
    if u.message and u.effective_chat.type == "private" and u.effective_user.id != OWNER_ID:
        info = await get_user_info(u)
        await c.bot.send_message(OWNER_ID, f"📩 **New Message:**\n\n{info}")
        await c.bot.copy_message(OWNER_ID, u.effective_chat.id, u.message.message_id)

    # Auto Reply
    if u.message and u.message.text:
        cur.execute("SELECT value FROM memory WHERE key = ?", (u.message.text.lower(),))
        res = cur.fetchone()
        if res: await u.message.reply_text(res[0])

async def welcome(u: Update, c: ContextTypes.DEFAULT_TYPE):
    for member in u.chat_member.new_chat_members:
        if member.id != c.bot.id:
            await u.effective_chat.send_message(f"ဟယ်... အချောလေး @{member.username or member.first_name} ရေ... ကြိုဆိုပါတယ်ရှင့်။ 🥰")

async def admin_tools(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    target = u.message.reply_to_message.from_user
    if '/ban' in u.message.text: await c.bot.ban_chat_member(u.effective_chat.id, target.id)
    elif '/mute' in u.message.text: await c.bot.restrict_chat_member(u.effective_chat.id, target.id, ChatPermissions(can_send_messages=False))
    await u.message.reply_text("အမိန့်တော်အတိုင်း ဆောင်ရွက်ပြီးပါပြီရှင့်။ 🫡")

async def love_match(u: Update, c: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT username FROM users WHERE chat_id = ?", (u.effective_chat.id,))
    data = cur.fetchall()
    if len(data) < 2: await u.message.reply_text("ဖူးစာရှင်လေးတွေ ရှာမတွေ့သေးဘူးရှင့်။"); return
    me = u.effective_user.username
    partner = random.choice(data)[0]
    await u.message.reply_text(f"💘 @{me} နဲ့ @{partner} မြှားနတ်မောင် ညားကြပါစေရှင့်! 🥰")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teach", teach))
    app.add_handler(CommandHandler(["ban", "mute"], admin_tools))
    app.add_handler(CommandHandler("love", love_match))
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL, forward_and_others))
    app.run_polling()

if __name__ == '__main__': main()
