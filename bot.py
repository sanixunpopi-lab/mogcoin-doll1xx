import asyncio
import logging
import os
import json
import asyncpg
from flask import Flask, request, jsonify
from flask_cors import CORS
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
import threading

# =============================================
# ===== НАСТРОЙКИ =====
# =============================================
BOT_TOKEN = "ТВОЙ_ТОКЕН_ОТ_BOTFATHER"
WEBAPP_URL = "https://твой_юзернейм.github.io/mog-coin/"
ADMIN_ID = 8698280423
DATABASE_URL = os.environ.get("DATABASE_URL")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)
CORS(app)

# ===== ПУЛ СОЕДИНЕНИЙ =====
db_pool = None

# =============================================
# ===== ИНИЦИАЛИЗАЦИЯ БАЗЫ =====
# =============================================
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                balance DOUBLE PRECISION DEFAULT 0,
                click_value DOUBLE PRECISION DEFAULT 0.000001,
                passive_value DOUBLE PRECISION DEFAULT 0,
                total_taps BIGINT DEFAULT 0,
                click_upgrades JSONB DEFAULT '[]',
                passive_upgrades JSONB DEFAULT '[]'
            )
        ''')
    logging.info("✅ База данных готова")

async def get_user(user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        if not row:
            await conn.execute('''
                INSERT INTO users (user_id, balance, click_value, passive_value)
                VALUES ($1, 0, 0.000001, 0)
            ''', user_id)
            row = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        return dict(row)

async def save_user(user_id, balance, click_value, passive_value, total_taps, click_upgrades, passive_upgrades):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, balance, click_value, passive_value, total_taps, click_upgrades, passive_upgrades)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (user_id) DO UPDATE SET
                balance = $2, click_value = $3, passive_value = $4,
                total_taps = $5, click_upgrades = $6, passive_upgrades = $7
        ''', user_id, balance, click_value, passive_value, total_taps,
            json.dumps(click_upgrades), json.dumps(passive_upgrades))

# =============================================
# ===== API ДЛЯ WEBAPP =====
# =============================================
@app.route('/balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        user = loop.run_until_complete(get_user(user_id))
    finally:
        loop.close()
    return jsonify(user), 200

@app.route('/balance/<int:user_id>', methods=['POST'])
def post_balance(user_id):
    data = request.get_json()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(save_user(
            user_id,
            data.get('balance', 0),
            data.get('clickValue', 0.000001),
            data.get('passiveValue', 0),
            data.get('totalTaps', 0),
            data.get('clickUpgrades', []),
            data.get('passiveUpgrades', [])
        ))
    finally:
        loop.close()
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index():
    return "Mog Coin API", 200

# =============================================
# ===== БОТ =====
# =============================================
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐸 Играть", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        "🐸 *Mog Coin*\n\nТапай и зарабатывай Mog Coin!",
        reply_markup=kb, parse_mode="Markdown"
    )

# =============================================
# ===== ЗАПУСК =====
# =============================================
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    await init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    logging.info("🚀 Flask запущен!")
    logging.info("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
