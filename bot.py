import asyncio
import logging
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
import threading

BOT_TOKEN = "8805424592:AAHVjlM6tuZ7pDT-1bpZ7yZDjfSxnDlRQl0"
WEBAPP_URL = "https://sanixunpopi-lab.github.io/mog-coin/"
ADMIN_ID = 8698280423

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Балансы (в памяти)
balances = {}

def get_bal(user_id): return balances.get(user_id, 0)
def set_bal(user_id, val): balances[user_id] = val

app = Flask(__name__)
CORS(app)

@app.route('/balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    return jsonify({"balance": get_bal(user_id)}), 200

@app.route('/balance/<int:user_id>', methods=['POST'])
def post_balance(user_id):
    data = request.get_json()
    set_bal(user_id, data.get('balance', 0))
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index(): return "Mog Coin API", 200

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐸 Играть", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        f"🐸 *Mog Coin*\n\nТапай и зарабатывай Mog Coin!\n\n💰 Баланс: {get_bal(message.from_user.id)}",
        reply_markup=kb, parse_mode="Markdown"
    )

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logging.info("🚀 Запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
