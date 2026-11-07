"""
Author: Bisnu Ray (Fixed Event Loop Error)
Telegram: https://t.me/SmartBisnuBio
"""

import os
import io
import logging
import threading
import PIL.Image
from flask import Flask
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from google import genai
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from config import API_ID, API_HASH, BOT_TOKEN, GOOGLE_API_KEY, MODEL_NAME, OWNER_ID

# ==================== FLASK WEB SERVER (Uptime Robot အတွက်) ====================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    # use_reloader=False က threading ထဲမှာ error မတက်အောင် ကာကွယ်ပေးသည်
    app_web.run(host="0.0.0.0", port=10000, use_reloader=False)

# Flask ကို Background Thread ဖြင့် စတင်ခြင်း
threading.Thread(target=run_web, daemon=True).start()


# ==================== PYROGRAM BOT SETUP ====================
app = Client(
    "gemini_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.MARKDOWN
)

client_ai = genai.Client(api_key=GOOGLE_API_KEY)

# Start မက်ဆေ့ဂျ်အတွက် ဗီဒီယို လင့်ခ် (သို့မဟုတ် File ID)
START_VIDEO_URL = "https://telegra.ph/file/xxxxxx.mp4" 

# User တစ်ဦးချင်းစီရဲ့ chat session တွေကို သိမ်းဆည်းရန်
user_chats = {}

def get_user_chat(user_id):
    if user_id not in user_chats:
        user_chats[user_id] = client_ai.chats.create(model=MODEL_NAME)
    return user_chats[user_id]


# 1. /start Command
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user = message.from_user
    
    user_name = user.first_name if user.first_name else "Not Provided"
    username = f"@{user.username}" if user.username else "မရှိပါ"
    user_id = user.id
    
    caption = (
        f"👋 မင်္ဂလာပါ **{user_name}** !\n\n"
        f"🤖 ကျွန်တော်ကတော့ သင်နဲ့အတူ စကားပြောဆိုပေးမယ့် AI Bot ဖြစ်ပါတယ်။\n\n"
        f"📌 **သင့်ရဲ့ အချက်အလက်များ:**\n"
        f"• အမည်: {user_name}\n"
        f"• Username: {username}\n"
        f"• User ID: `{user_id}`\n\n"
        f"👇 အောက်ပါခလုတ်များကို အသုံးပြုနိုင်ပါတယ်။"
    )
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Developer သို့ ဆက်သွယ်ရန်", url="https://t.me/SmartBisnuBio")],
        [InlineKeyboardButton("🗑️ မှတ်ဉာဏ်ရှင်းရန် (Reset)", callback_data="reset_chat")]
    ])
    
    try:
        await message.reply_video(
            video=START_VIDEO_URL,
            caption=caption,
            reply_markup=reply_markup
        )
    except Exception:
        await message.reply_text(caption, reply_markup=reply_markup)


# 2. Callback Query
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if callback_query.data == "reset_chat":
        if user_id in user_chats:
            del user_chats[user_id]
        await callback_query.answer("🔄 Chat history has been reset!", show_alert=True)
        await callback_query.message.edit_caption("🔄 **Chat history reset လုပ်ပြီးပါပြီ။ ဆက်လက်မေးမြန်းနိုင်ပါပြီ။**")


# 3. ADMIN COMMAND (/setvideo)
@app.on_message(filters.command("setvideo") & filters.user(OWNER_ID))
async def set_video_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.video:
        await message.reply_text("❌ ကျေးဇူးပြု၍ ဗီဒီယိုဖိုင်တစ်ခုကို Reply လုပ်ပြီး `/setvideo` ဟု ရိုက်ပါ။")
        return
    
    video_file_id = message.reply_to_message.video.file_id
    await message.reply_text(f"✅ **Start ဗီဒီယို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ!**\n\nFile ID:\n`{video_file_id}`")


# 4. Direct AI Chat
@app.on_message(filters.text & ~filters.command(["reset", "imgai", "setvideo"]))
async def direct_chat_handler(client: Client, message: Message):
    if message.text.startswith("/"):
        return

    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)

        prompt = message.text
        user_id = message.from_user.id
        
        chat = get_user_chat(user_id)
        response = chat.send_message(prompt)

        response_text = response.text
        if len(response_text) > 4000:
            parts = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
            for part in parts:
                await message.reply_text(part)
        else:
            await message.reply_text(response_text)

    except Exception as e:
        await message.reply_text(f"**An error occurred: {str(e)}**")


# 5. Image Analysis (/imgai)
@app.on_message(filters.command("imgai"))
async def generate_from_image(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("**Please reply to a photo for a response.**")
        return

    prompt = message.command[1] if len(message.command) > 1 else message.reply_to_message.caption or "Describe this image."
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        img_data = await client.download_media(message.reply_to_message, in_memory=True)
        img = PIL.Image.open(io.BytesIO(img_data.getbuffer()))

        response = client_ai.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, img],
        )
        response_text = response.text

        await message.reply_text(response_text, parse_mode=None)
    except Exception as e:
        logging.error(f"Error during image analysis: {e}")
        await message.reply_text("**An error occurred. Please try again.**")


if __name__ == '__main__':
    # Pyrogram Bot ကို Main Thread တွင် ပုံမှန်အတိုင်း စတင် Run မည်
    app.run()
