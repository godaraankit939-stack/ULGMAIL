import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# Environment Variables
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
            [InlineKeyboardButton("Male", callback_data="1"), InlineKeyboardButton("Female", callback_data="2")]
        ])
        await message.reply("Select **Gender**:", reply_markup=btn)
    elif step == "USERNAME":
        state["username"] = message.text.lower().replace(" ", "")
        state["step"] = "PASSWORD"
        await message.reply("Set a **Password**:")
    elif step == "PASSWORD":
        state["password"] = message.text
        status_msg = await message.reply("⏳ **Starting Automation Engine...**")
        asyncio.create_task(gmail_engine(status_msg, state))
        del USER_STATE[user_id]

@bot.on_callback_query()
async def callback_worker(client, callback):
    user_id = callback.from_user.id
    if user_id in USER_STATE:
        USER_STATE[user_id]["gender"] = callback.data
        USER_STATE[user_id]["step"] = "USERNAME"
        await callback.message.edit("Enter desired **Gmail ID** (without @gmail.com):")

async def gmail_engine(status_msg, data):
    async with async_playwright() as p:
        try:
            await status_msg.edit("🌐 **Launching Stealth Browser...**")
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36")
            page = await context.new_page()
            await stealth_async(page)
            
            # --- STEP 1: LOAD SIGNUP ---
            await status_msg.edit("📄 **Loading Google Signup Page...**")
            await page.goto("https://accounts.google.com/signup", timeout=60000)
            
            # --- STEP 2: FILL NAMES ---
            await status_msg.edit("✍️ **Filling Names...**")
            await page.fill('input[name="firstName"]', data["first_name"])
            await page.fill('input[name="lastName"]', data["last_name"])
            await page.click('button:has-text("Next"), #collectNameNext')
            await asyncio.sleep(3)

            # --- STEP 3: FILL DOB ---
            await status_msg.edit("📅 **Filling Date of Birth & Gender...**")
            day, month, year = data["dob"].split('/')
            await page.fill('input[name="day"]', day)
            await page.select_option('select#month', value=str(int(month)))
            await page.fill('input[name="year"]', year)
            await page.select_option('select#gender', value=data["gender"])
            await page.click('button:has-text("Next"), #basicDegNext')
            await asyncio.sleep(3)

            # --- STEP 4: USERNAME ---
            await status_msg.edit("🔍 **Selecting Username...**")
            if await page.is_visible('input[name="Username"]'):
                await page.fill('input[name="Username"]', data["username"])
            else:
                await page.click('div[role="radio"]:last-child') 
            await page.click('button:has-text("Next"), #next')
            await asyncio.sleep(3)

            # --- STEP 5: PASSWORD ---
            await status_msg.edit("🔐 **Setting Password...**")
            await page.fill('input[name="Passwd"]', data["password"])
            await page.fill('input[name="ConfirmPasswd"]', data["password"])
            await page.click('button:has-text("Next")')
            await asyncio.sleep(5)

            # --- STEP 6: SECURITY CHECK ---
            await status_msg.edit("🛡️ **Checking for Phone Verification...**")
            if "phone" in page.url.lower() or await page.query_selector('input[type="tel"]'):
                await status_msg.edit("❌ **Atka Hai:** Google is asking for a **Phone Number**. Railway IP blocked.")
            else:
                await status_msg.edit(f"✅ **Account Created!**\nEmail: `{data['username']}@gmail.com`")

        except Exception as e:
            await status_msg.edit(f"⚠️ **Error At:** `{str(e)[:100]}`")
        finally:
            await browser.close()

if __name__ == "__main__":
    bot.run()
    
