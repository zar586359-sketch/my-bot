import logging, os, asyncio, random
from flask import Flask
from threading import Thread
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes)

# --- Keep Alive ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "မြနှင်း Bot Online ❤️"
Thread(target=lambda: app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()

# --- Config ---
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 7771663458
CHANNEL_ID = -1001234567890 
group_list, memory, registered_users, spam_count = {}, {}, {}, {}

def get_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Bot ကို Group ထည့်ရန်", url="https://t.me/Cupi677Bot?startgroup=true")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/BOTUAPTE")],
        [InlineKeyboardButton("👑 Owner @Tear808", url="https://t.me/Tear808")]
    ])

# --- Functions ---
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user = u.effective_user
    info = f"🚀 **New Start**\n👤 Name: {user.full_name}\n🆔 ID: `{user.id}`\n🔗 User: @{user.username}"
    await c.bot.send_message(OWNER_ID, info, parse_mode='Markdown')
    msg = f"🎀 မင်္ဂလာပါ {user.first_name}!\nမြနှင်း (`Cupi677Bot`) အသင့်ရှိပါပြီရှင့်! 😍"
    await u.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_buttons())

async def welcome_goodbye(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat = u.effective_chat
    group_list[chat.id] = chat.title
    if u.message.new_chat_members:
        for m in u.message.new_chat_members:
            if m.id != c.bot.id: await chat.send_message(f"🎀 {m.full_name} ရေ... ကြိုဆိုပါတယ်ရှင့်သူမလိုပဲပုံပြင်မပြောခဲ့ကျေးနော်! 😍")
    elif u.message.left_chat_member:
        await chat.send_message(f"🥺 {u.message.left_chat_member.full_name} ထွက်သွားပြီ... အလွမ်းတွေနဲ့ စောင့်နေမယ်နော်‌ေနာက်လူရင်ခွင်မှာမ‌ေပျာ်ရင်ပြန်လာခဲ့ပ😊။ 💔")

async def admin_tools(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message.reply_to_message: return
    target = u.message.reply_to_message.from_user
    cmd = u.message.text.lower()
    if '/ban' in cmd: await c.bot.ban_chat_member(u.effective_chat.id, target.id)
    elif '/mute' in cmd: 
        await c.bot.restrict_chat_member(u.effective_chat.id, target.id, ChatPermissions(can_send_messages=False))
        await u.message.reply_text(f"🤫 @{target.username} ကို (၁) နာရီ Mute လိုက်ပါပြီရှာရှည်လို့။")
        c.job_queue.run_once(lambda ctx: ctx.bot.restrict_chat_member(u.effective_chat.id, target.id, ChatPermissions(can_send_messages=True)), 3600)
    elif '/admin' in cmd:
        admins = await c.bot.get_chat_administrators(u.effective_chat.id)
        mentions = " ".join([f"@{a.user.username}" for a in admins if a.user.username])
        await u.message.reply_text(f"📣 Admin လေးတို့ရေ နာရီ! 🆘\n{mentions}")

async def broadcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id == OWNER_ID and u.message.reply_to_message:
        for gid in group_list:
            try: await c.bot.copy_message(gid, u.effective_chat.id, u.message.reply_to_message.message_id)
            except: continue

async def register(u: Update, c: ContextTypes.DEFAULT_TYPE):
    gender = "Boy" if "boy" in u.message.text.lower() else "Girl"
    if u.effective_chat.id not in registered_users: registered_users[u.effective_chat.id] = {}
    registered_users[u.effective_chat.id][u.effective_user.id] = {"username": f"@{u.effective_user.username}", "gender": gender}
    await u.message.reply_text(f"✨ {gender} အဖြစ် မှတ်တမ်းတင်ပြီးပါပြီ!")

async def love_match(u: Update, c: ContextTypes.DEFAULT_TYPE):
    potential = [d for uid, d in registered_users.get(u.effective_chat.id, {}).items() if uid != u.effective_user.id]
    if potential: await u.message.reply_text(f"💘 တွေ့ပြီ! {random.choice(potential)['username']} နဲ့ ညားကြပါစေ!")

async def message_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.type == "private" and u.effective_user.id != OWNER_ID:
        await c.bot.copy_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
    text = u.message.text.lower() if u.message.text else ""
    if text.startswith("/teach "):
        parts = text.split(" ", 2)
        if len(parts) == 3: memory[parts[1]] = parts[2]; await u.message.reply_text("✅ မှတ်သားလိုက်ပြီ!")
    elif text in memory: await u.message.reply_text(memory[text])
    
    # Anti-Spam
    if u.effective_chat.type != "private" and u.effective_user.id != OWNER_ID:
        uid = u.effective_user.id
        spam_count[uid] = spam_count.get(uid, 0) + 1
        if spam_count[uid] >= 3:
            await u.message.delete()
            await c.bot.restrict_chat_member(u.effective_chat.id, uid, ChatPermissions(can_send_messages=False))
            c.job_queue.run_once(lambda ctx: ctx.bot.restrict_chat_member(u.effective_chat.id, uid, ChatPermissions(can_send_messages=True)), 3600)
            spam_count[uid] = 0

def main():
    app = Application.builder().token(TOKEN).build()
    app.job_queue.start()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["ban", "mute", "admin"], admin_tools))
    app.add_handler(CommandHandler("bcast", broadcast))
    app.add_handler(CommandHandler(["boy", "girl"], register))
    app.add_handler(CommandHandler("love", love_match))
    app.add_handler(ChatMemberHandler(welcome_goodbye, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.run_polling()

if __name__ == '__main__': main()
  
