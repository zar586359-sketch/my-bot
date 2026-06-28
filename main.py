import logging
import os
import random
from flask import Flask
from threading import Thread
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Keep Alive ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "မြနှင်း Bot Online ❤️"

def run():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Settings & Data ---
TOKEN = os.environ.get("BOT_TOKEN") 
OWNER_ID = 7771663458  
registered_users = {} 
group_list = {}

AD_TEXT = (
    "\n\n━━━━━━━━━━━━━━\n"
    "📢 https://t.me/+FFbLsHyYIAg4YmU1\n"
    "ရည်းစားရှာဖွေရေး gp ကို join ပေးကျပါရှင့် 🥰😘✅"
)

logging.basicConfig(level=logging.INFO)

async def is_admin_or_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == "private": return False
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status in ['administrator', 'creator']
    except: return False

# --- ✨ လူသစ်ဝင်လာရင် ကြိုဆိုခြင်း ---
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members: return
    chat = update.effective_chat
    group_list[chat.id] = chat.title
    for member in update.message.new_chat_members:
        if member.id == context.bot.id: continue
        username = f"@{member.username}" if member.username else f"[{member.first_name}](tg://user?id={member.id})"
        welcome_msg = (
            f"ဟယ်... အချောလေး {username} ရေ... 😍✨\n"
            f"ငါတို့ GP ထဲ ရောက်လာပြီဟယ်... ချောလိုက်တာနော် ချစ်စရာလေး။ 🥰💋\n\n"
            f"🎀 **မြနှင်း** ရဲ့ နွေးထွေးတဲ့ ရင်ခွင်ထဲကို ကြိုဆိုပါတယ်ရှင့်။"
        )
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

# --- 💖 မြှားနတ်မောင် ---
async def love_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if chat_id not in registered_users or user_id not in registered_users[chat_id]:
        await update.message.reply_text("🚨 အရင်ဆုံး /boy ဒါမှမဟုတ် /girl နဲ့ စာရင်းသွင်းပါဦး သဲလေးရဲ့... 🥺💗")
        return
    me = registered_users[chat_id][user_id]
    potential = [uid for uid, data in registered_users[chat_id].items() if uid != user_id and data["gender"] != me["gender"]]
    if not potential:
        await update.message.reply_text("⏳ ဖူးစာရှင်လေးတွေ ရှာမတွေ့သေးဘူးရှင့်... 🥺💕")
        return
    partner = registered_users[chat_id][random.choice(potential)]
    match_msg = (
        f"💘 **မြှားနတ်မောင် မြှားပစ်လိုက်ပြီရှင့်** 🏹🎯✨\n\n"
        f"❤️ {me['username']}  ❤️ {partner['username']}\n\n"
        f"မြန်မြန်လေး ညားကြပါစေရှင့်! 🥰\n"
        f"**နောင်တစ်သက်လုံးလည်း အချစ်တွေ တိုးပွားပါစေရှင့်!** 🤪🔥💕💋✨"
    )
    await update.message.reply_text(match_msg, parse_mode='Markdown')

# --- 🛡 အရေးပေါ် Admin Tools ---
async def admin_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_owner(update, context): return
    if not update.message.reply_to_message: return
    target = update.message.reply_to_message.from_user
    cmd = update.message.text.lower()
    try:
        if '/ban' in cmd:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            await update.message.reply_text(f"🚨 **သဲလေးရဲ့ အမိန့်တော်ပါရှင်** 🚨\n\n@{target.username} ရေ... နင်က ဒီ Group လေးနဲ့ မတန်ပါဘူးကွာ... အပြီးအပိုင် ထွက်သွားပေးတော့နော်! 🤬💢🔥")
        elif '/mute' in cmd:
            await context.bot.restrict_chat_member(update.effective_chat.id, target.id, ChatPermissions(can_send_messages=False))
            await update.message.reply_text(f"🤫 **ချစ်စရာလေးရဲ့ အမိန့်** 🤫\n\n@{target.username} ရေ... စကားတွေ အရမ်းများနေလို့ သဲလေး စိတ်ညစ်ရတယ်... ခဏလေးတော့ အသံတိတ်ပြီး လိမ်လိမ်မာမာလေး နေပေးပါဦးနော်! 🤐🔇🚫")
        elif '/umute' in cmd:
            await context.bot.restrict_chat_member(update.effective_chat.id, target.id, ChatPermissions(can_send_messages=True))
            await update.message.reply_text(f"🔊 **ပြန်ချစ်ပေးလိုက်ပြီနော်** 🔊\n\n@{target.username} ရေ... အခုတော့ လိမ်မာသွားပြီထင်လို့ ပြန်ပြီး စကားလေး ပြောခွင့်ပေးလိုက်ပါပြီနော်... အာဘွား! 😘✅✨")
    except: pass

# --- 📢 Admin ခေါ်ရန် ---
async def call_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        mentions = " ".join([f"@{a.user.username}" for a in admins if a.user.username])
        await update.message.reply_text(f"📣📣 **Admin လေးတို့ရေ...gp‌မှာပြဿနာ‌များဖစ်နေသဖြင့်** 🥰\n\nအမြန်လာကျရန်ownerအမိန့်စာ🫅... မြန်မြန်လေး လာခဲ့ပေးပါဦးနော်... သဲလေး စောင့်နေလို့ပါရှင့်... အာဘွား! 💋✨\n\n{mentions}")
    except: pass

# --- 🚀 Broadcast (Owner သီးသန့်) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not update.message.reply_to_message:
        await update.message.reply_text("💡 ဖြန့်မယ့်စာကို Reply ပြန်ပြီး /bcast ရိုက်ပါရှင့်")
        return
    
    target_msg = update.message.reply_to_message
    success = 0
    total = len(group_list)
    
    await update.message.reply_text(f"⏳ စတင်ပို့ဆောင်နေပါပြီနတ်သားလေး... (GP စုစုပေါင်း: {total} ခု)")
    
    for chat_id in list(group_list.keys()):
        try:
            await context.bot.copy_message(chat_id=chat_id, from_chat_id=update.effective_chat.id, message_id=target_msg.message_id)
            success += 1
        except:
            continue
    await update.message.reply_text(f"✅ ပို့ဆောင်မှု ပြီးဆုံးပါပြီရှင့်! \n🎯 စုစုပေါင်း {total} ခုထဲမှ {success} ခုသို့ အောင်မြင်စွာ ပို့ပေးလိုက်ပါပြီရှင့်owner။ 🥰")

# --- Start & Help ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]: group_list[update.effective_chat.id] = update.effective_chat.title
    start_msg = f"မဂ်လာပါရှင့် 😘\n\n🎀**မြနှင်း**🎀 ကို Group ထဲထည့်ပေးပါနော်။ အာဘွား😘 သဲယေး👉🥺👈။\nအသုံးပြုပုံကြည့်ရန် - /help နှိပ်ပေးပါရှင့်။ကြောညာထည့်ရန်owner @Tear808 🫅✅✅1post_1500kyat-3000kyat✅❤️‍🩹{AD_TEXT}"
    await update.message.reply_text(start_msg, parse_mode='Markdown')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = "✨ **မြနှင်း နတ်သား/နတ်သမီး 🤵👰အသုံးပြုရန်လမ်းညွှန်** ✨\n\n👤 /boy , /girl - စာရင်းသွင်းရန်\n💖 /love - မြှားနတ်မောင်ချိပ်ရန်\n📢 /admin -gp Admin နတ်သား/နတ်သမီးခေါ်ရန်\n\n🛡 **Admin Tools (GP Admin များအတွက်)**\n🚫 /ban-ကစ်ထုပ်ရန်ခွေးကို , 🤫 /mute-စောက်စကားများနေရင်လုပ် , 🔊 /umute-လိမ်မာသွားပီဖွင့်ပေးမယ်"
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    if not user.username: await update.message.reply_text("❌ Username အရင်ဆောက်ပေးပါဦးနော်မ‌ေဆာက်ရင်အရမ်းချစ်တယ်ထားမသွာစဘူး။"); return
    gender = "Boy 👨" if "boy" in update.message.text.lower() else "Girl 👩"
    if chat_id not in registered_users: registered_users[chat_id] = {}
    registered_users[chat_id][user.id] = {"username": f"@{user.username}", "gender": gender}
    await update.message.reply_text(f"✨ {gender} အဖြစ် မှတ်တမ်းတင်လိုက်ပြီနော်ချောချောလေးတွေပာစေ! 🥰")

def main():
    if not TOKEN: return
    keep_alive()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("admin", call_admin))
    app.add_handler(CommandHandler("bcast", broadcast))
    app.add_handler(CommandHandler(["boy", "girl"], register))
    app.add_handler(CommandHandler("love", love_match))
    app.add_handler(CommandHandler(["ban", "mute", "umute"], admin_tools))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, lambda u, c: group_list.update({u.effective_chat.id: u.effective_chat.title})))
    app.run_polling()

if __name__ == '__main__': main()
      
