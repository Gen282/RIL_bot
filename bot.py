import asyncio
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8634847926:AAGIacapMgyqULHlggnv9dAKtJAlbm2Pb5"
ADMIN_ID = 8296841503

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

counter_file = "counter.txt"
orders_file = "orders.json"

def get_num():
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as f:
            n = int(f.read())
    else:
        n = 99
    n += 1
    with open(counter_file, 'w') as f:
        f.write(str(n))
    return n

def save_order(oid, data):
    orders = {}
    if os.path.exists(orders_file):
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders = json.load(f)
    orders[str(oid)] = data
    with open(orders_file, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def get_order(oid):
    if os.path.exists(orders_file):
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders = json.load(f)
        return orders.get(str(oid))
    return None

class CreateOrder(StatesGroup):
    link = State()
    name = State()
    address = State()
    phone = State()

def main_menu():
    kb = [
        [InlineKeyboardButton(text="🛒 Новый заказ", callback_data="new")],
        [InlineKeyboardButton(text="🔍 Статус заказа", callback_data="status")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(msg, state):
    await state.clear()
    await msg.answer("👋 Бот RIL cashier\n\nВыберите действие:", reply_markup=main_menu())

@dp.callback_query(F.data == "new")
async def new_order(cb, state):
    await state.clear()
    await cb.message.edit_text("Отправьте ссылку на товар:")
    await state.set_state(CreateOrder.link)
    await cb.answer()

@dp.message(CreateOrder.link)
async def get_link(msg, state):
    await state.update_data(link=msg.text)
    await msg.answer("Ваше имя:")
    await state.set_state(CreateOrder.name)

@dp.message(CreateOrder.name)
async def get_name(msg, state):
    await state.update_data(name=msg.text)
    await msg.answer("Адрес:")
    await state.set_state(CreateOrder.address)

@dp.message(CreateOrder.address)
async def get_address(msg, state):
    await state.update_data(address=msg.text)
    await msg.answer("Телефон:")
    await state.set_state(CreateOrder.phone)

@dp.message(CreateOrder.phone)
async def get_phone(msg, state):
    data = await state.get_data()
    num = get_num()
    order = {
        'id': num,
        'user_id': msg.from_user.id,
        'user_name': msg.from_user.full_name,
        'link': data['link'],
        'name': data['name'],
        'address': data['address'],
        'phone': msg.text,
        'status': 'Принят',
        'created': datetime.now().isoformat()
    }
    save_order(num, order)
    await msg.answer(f"✅ Заказ #{num} принят!", reply_markup=main_menu())
    admin_text = f"🛒 ЗАКАЗ #{num}\n\nКлиент: {msg.from_user.full_name}\nСсылка: {data['link']}\nИмя: {data['name']}\nАдрес: {data['address']}\nТелефон: {msg.text}"
    await bot.send_message(ADMIN_ID, admin_text)
    await state.clear()

@dp.callback_query(F.data == "status")
async def status_prompt(cb):
    await cb.message.edit_text("Введите номер заказа:")
    await cb.answer()

@dp.message(F.text.isdigit())
async def check_status(msg):
    oid = int(msg.text)
    o = get_order(oid)
    if not o:
        await msg.answer(f"Заказ #{oid} не найден", reply_markup=main_menu())
        return
    await msg.answer(f"Заказ #{oid}\nСтатус: {o.get('status', 'Принят')}", reply_markup=main_menu())

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
