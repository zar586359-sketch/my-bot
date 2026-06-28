import logging, os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- Keep Alive ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is Online"
Thread(target=lambda: app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()

# --- Config ---
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 7771663458
CHANNEL_ID = -1003841480184
group_list = {}

# --- 1. Welcome / Goodbye ---
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(f"ဟယ်... {member.first_name} ရေ... 🎀 **မြနှင်း** ရဲ့ ရင်ခွင်ထဲကို ကြိုဆိုပါတယ်ရှင့်။ 😍")
        group_list[update.effective_chat.id] = update.effective_chat.title

# --- 2. Link Delete ---
async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID: return
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type in ['url', 'text_link']:
                await update.message.delete()
                await update.message.reply_text("🚫 Link တင်ခြင်း ခွင့်မပြုပါရှင့်!")

# --- 3. Start & Buttons ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📢 Channel", url="https://t.me/BOTUAPTE"), InlineKeyboardButton("🫅 Owner", url="https://t.me/Tear808")]]
    await update.message.reply_text("🎀 မင်္ဂလာပါရှင့်! မြနှင်း Bot အသင့်ရှိပါပြီ။", reply_markup=InlineKeyboardMarkup(kb))

# --- 4. Forward & Broadcast ---
async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.chat.id == CHANNEL_ID:
        for gid in group_list:
            try: await context.bot.copy_message(gid, CHANNEL_ID, update.channel_post.message_id)
            except: continue
    if update.effective_chat and update.effective_chat.type in ["group", "supergroup"]:
        group_list[update.effective_chat.id] = update.effective_chat.title

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or not update.message.reply_to_message: return
    msg_id = update.message.reply_to_message.message_id
    for gid in group_list:
        try: await context.bot.copy_message(gid, update.effective_chat.id, msg_id)
        except: continue
    await update.message.reply_text("✅ ပို့ဆောင်မှုပြီးပါပြီ။")

# --- 5. Admin Tools ---
async def admin_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return
    target = update.message.reply_to_message.from_user
    cmd = update.message.text.lower()
    if '/ban' in cmd: await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    elif '/mute' in cmd: await context.bot.restrict_chat_member(update.effective_chat.id, target.id, ChatPermissions(can_send_messages=False))
    elif '/umute' in cmd: await context.bot.restrict_chat_member(update.effective_chat.id, target.id, ChatPermissions(can_send_messages=True))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bcast", broadcast))
    app.add_handler(CommandHandler(["ban", "mute", "umute"], admin_tools))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    app.add_handler(MessageHandler(filters.Entity("url") | filters.Entity("text_link"), delete_links))
    app.add_handler(MessageHandler(filters.ALL, forward_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
