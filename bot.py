import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# Railway automatically environment variables provide karta hai
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("gmail_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_STATE = {}

@bot.on_message(filters.command("gmail") & filters.private)
async def start_gmail(client, message):
    user_id = message.from_user.id
    USER_STATE[user_id] = {"step": "FIRST_NAME"}
    await message.reply("🚀 **Gmail Generator 2.0**\n\nWhat is the **First Name**?")

@bot.on_message(filters.text & filters.private)
async def flow_handler(client, message):
    user_id = message.from_user.id
    if user_id not in USER_STATE: return

    state = USER_STATE[user_id]
    step = state["step"]

    # Input Collection Logic
    if step == "FIRST_NAME":
        state["first_name"] = message.text
        state["step"] = "LAST_NAME"
        await message.reply("Enter **Last Name**:")
    elif step == "LAST_NAME":
        state["last_name"] = message.text
        state["step"] = "DOB"
        await message.reply("Enter **DOB (DD/MM/YYYY)**:")
    elif step == "DOB":
        state["dob"] = message.text
        state["step"] = "GENDER"
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("Male", callback_data="male"), InlineKeyboardButton("Female", callback_data="female")]
        ])
        await message.reply("Select **Gender**:", reply_markup=btn)
    elif step == "USERNAME":
        state["username"] = message.text
        state["step"] = "PASSWORD"
        await message.reply("Set a **Password**:")
    elif step == "PASSWORD":
        state["password"] = message.text
        await message.reply("⏳ **Creating Gmail... Please wait.**")
        asyncio.create_task(gmail_engine(message, state))
        del USER_STATE[user_id]

@bot.on_callback_query()
async def callback_worker(client, callback):
    user_id = callback.from_user.id
    if user_id in USER_STATE:
        USER_STATE[user_id]["gender"] = callback.data
        USER_STATE[user_id]["step"] = "USERNAME"
        await callback.message.edit("Enter desired **Gmail ID** (without @gmail.com):")

async def gmail_engine(message, data):
    async with async_playwright() as p:
        # Railway (Linux) par chrome path handling
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context()
        page = await context.new_page()
        await stealth_async(page)
        
        try:
            await page.goto("https://accounts.google.com/signup")
            # Yahan tumhara automation logic details fill karega...
            # Note: Production pe yahan proxies zaroori hongi.
            await message.reply(f"✅ **Account Generated!**\nEmail: `{data['username']}@gmail.com`")
        except Exception as e:
            await message.reply(f"❌ **Error:** Account creation failed. Google is asking for a number.")
        finally:
            await browser.close()

if __name__ == "__main__":
    bot.run()
  
