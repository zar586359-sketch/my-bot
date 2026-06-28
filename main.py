import logging, os, asyncio, random
from flask import Flask
from threading import Thread
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- Keep Alive ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is Online"
Thread(target=lambda: app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()

# --- Config ---
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 7771663458
CHANNEL_ID = -1003841480184
memory, spam_count, registered_users = {}, {}, {}

# --- Admin Tools ---
async def admin_tools(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message.reply_to_message: return
    target = u.message.reply_to_message.from_user
    cmd = u.message.text.lower()
    if '/ban' in cmd: await c.bot.ban_chat_member(u.effective_chat.id, target.id)
    elif '/mute' in cmd:
        await c.bot.restrict_chat_member(u.effective_chat.id, target.id, ChatPermissions(can_send_messages=False))
        c.job_queue.run_once(lambda ctx: ctx.bot.restrict_chat_member(u.effective_chat.id, target.id, ChatPermissions(can_send_messages=True)), 3600)

# --- Broadcast & Love Match ---
async def broadcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id == OWNER_ID and u.message.reply_to_message:
        await u.message.reply_text("✅ ကြော်ငြာစာ ပို့ပြီးပါပြီ။")

async def register(u: Update, c: ContextTypes.DEFAULT_TYPE):
    gender = "Boy" if "boy" in u.message.text.lower() else "Girl"
    if u.effective_chat.id not in registered_users: registered_users[u.effective_chat.id] = {}
    registered_users[u.effective_chat.id][u.effective_user.id] = {"username": f"@{u.effective_user.username}", "gender": gender}
    await u.message.reply_text(f"✨ {gender} အဖြစ် မှတ်တမ်းတင်ပြီးပါပြီ!")

async def love_match(u: Update, c: ContextTypes.DEFAULT_TYPE):
    potential = [d for uid, d in registered_users.get(u.effective_chat.id, {}).items() if uid != u.effective_user.id]
    if potential: await u.message.reply_text(f"💘 တွေ့ပြီ! {random.choice(potential)['username']} နဲ့ ညားကြပါစေ!")

# --- Core Handler ---
async def message_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # 1. Group to Channel Fwd
    if u.effective_chat.type in ["group", "supergroup"] and u.message:
        try: await c.bot.forward_message(CHANNEL_ID, u.effective_chat.id, u.message.message_id)
        except: pass

    # 2. Private Fwd to Owner
    if u.effective_chat.type == "private" and u.effective_user.id != OWNER_ID:
        await c.bot.copy_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
    
    # 3. Auto Reply (/teach)
    text = u.message.text.lower() if u.message.text else ""
    if text.startswith("/teach "):
        parts = text.split(" ", 2)
        if len(parts) == 3: memory[parts[1]] = parts[2]; await u.message.reply_text("✅ မှတ်သားလိုက်ပြီ!")
    elif text in memory: await u.message.reply_text(memory[text])

    # 4. Anti-Spam
    if u.effective_chat.type != "private" and u.effective_user.id != OWNER_ID:
        uid = u.effective_user.id
        spam_count[uid] = spam_count.get(uid, 0) + 1
        if spam_count[uid] >= 3:
            await u.message.delete()
            await c.bot.restrict_chat_member(u.effective_chat.id, uid, ChatPermissions(can_send_messages=False))
            c.job_queue.run_once(lambda ctx: ctx.bot.restrict_chat_member(u.effective_chat.id, uid, ChatPermissions(can_send_messages=True)), 3600)
            spam_count[uid] = 0

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["ban", "mute"], admin_tools))
    app.add_handler(CommandHandler("bcast", broadcast))
    app.add_handler(CommandHandler(["boy", "girl"], register))
    app.add_handler(CommandHandler("love", love_match))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.run_polling()

if __name__ == '__main__': main()
  
