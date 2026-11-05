"""
Telegram Bot for UZEX AI Hackathon 2026.
Built with aiogram 3. Responds to natural language queries in Uzbek and Russian with full provenance.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from src.config import TELEGRAM_BOT_TOKEN
from src.agent import UzexAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

agent = UzexAgent()
dp = Dispatcher()

# User language preferences
user_languages: Dict[int, str] = {}

def get_welcome_kb(lang: str = 'uz') -> InlineKeyboardMarkup:
    if lang == 'ru':
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Топ-5 продавцов цемента 2024", callback_data="q_cement"),
                InlineKeyboardButton(text="🏢 Код BK001", callback_data="q_bk001")
            ],
            [
                InlineKeyboardButton(text="🚫 Аннулированные сделки 2023", callback_data="q_cancel"),
                InlineKeyboardButton(text="📊 Общая статистика", callback_data="btn_stats")
            ],
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekchaga o'tish", callback_data="set_lang_uz")
            ]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 2024 eng ko'p sement sotganlar", callback_data="q_cement"),
            InlineKeyboardButton(text="🏢 BK001 kodi haqida", callback_data="q_bk001")
        ],
        [
            InlineKeyboardButton(text="🚫 2023 bekor qilingan bitimlar", callback_data="q_cancel"),
            InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="btn_stats")
        ],
        [
            InlineKeyboardButton(text="🇷🇺 Перейти на русский", callback_data="set_lang_ru")
        ]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'uz')
    
    if lang == 'ru':
        text = (
            "👋 **Здравствуйте!** Я официальный AI-ассистент по биржевым сделкам **UZEX**.\n\n"
            "Я знаю всё о **500 000 сделках** (2022–2026 гг.) на товарно-сырьевой бирже spot.uzex.uz.\n\n"
            "🔍 **Мои возможности:**\n"
            "• Точные цифры, объёмы, суммы и цены по товарам\n"
            "• Поиск компаний по ИНН и названию\n"
            "• Информация о брокерских конторах (BK001–BK120)\n"
            "• Статистика по регионам и статусам сделок\n"
            "• Строго факты — без галлюцинаций и выдумок!\n\n"
            "💡 Напишите ваш вопрос или выберите готовый пример:"
        )
    else:
        text = (
            "👋 **Assalomu alaykum!** Men **UZEX** birja bitimlari bo'yicha sun'iy intellekt yordamchisiman.\n\n"
            "Men spot.uzex.uz birjasidagi **500 000 ta bitim** (2022–2026 yillar) bo'yicha barcha savollarga aniq va faqat faktlar asosida javob beraman.\n\n"
            "🔍 **Imkoniyatlarim:**\n"
            "• Tovar hajmlari, summalari va o'rtacha narxlar\n"
            "• Kompaniyalarni STIR (INN) va nomi bo'yicha tahlil qilish\n"
            "• Brokerlik idoralari ma'lumotlari (BK001–BK120)\n"
            "• Hududlar va bitim holatlari bo'yicha statistika\n"
            "• Gallyutsinatsiyasiz, 100% ishonchli va shaffof ma'lumotlar!\n\n"
            "💡 Savolingizni yozing yoki quyidagi namunalardan birini tanlang:"
        )
    await message.answer(text, reply_markup=get_welcome_kb(lang), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'uz')
    con = agent.db_engine.get_connection()
    stats = con.execute("""
        SELECT 
            count(*) as total_deals,
            round(sum(deal_amount_uzs) / 1e12, 2) as total_trln,
            min(deal_date),
            max(deal_date)
        FROM deals
    """).fetchone()
    
    if lang == 'ru':
        msg = (
            "📊 **Статистика реестра UZEX (2022-2026):**\n\n"
            f"• **Всего сделок:** `{stats[0]:,}`\n".replace(",", " ") +
            f"• **Общий оборот:** `{stats[1]} Трлн сум`\n"
            f"• **Период:** `03.01.2022 — 30.10.2026`\n"
            "• **Карточек контрактов:** `6 616`\n"
            "• **Участников торгов:** `14 392`\n"
            "• **Брокерских контор:** `120`"
        )
    else:
        msg = (
            "📊 **UZEX birja reyestri statistikasi (2022-2026):**\n\n"
            f"• **Jami bitimlar soni:** `{stats[0]:,}` ta\n".replace(",", " ") +
            f"• **Umumiy savdo aylanmasi:** `{stats[1]} Trln so'm`\n"
            f"• **Qamrov davri:** `03.01.2022 — 30.10.2026`\n"
            "• **Shartnoma kartochkalari:** `6 616 ta`\n"
            "• **Ishtirokchi kompaniyalar:** `14 392 ta`\n"
            "• **Brokerlik idoralari:** `120 ta`"
        )
    await message.answer(msg, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data.startswith("set_lang_"))
async def cb_lang(callback: types.CallbackQuery):
    new_lang = 'uz' if callback.data == 'set_lang_uz' else 'ru'
    user_languages[callback.from_user.id] = new_lang
    ack = "🇺🇿 Til o'zbekchaga o'zgartirildi!" if new_lang == 'uz' else "🇷🇺 Язык изменён на русский!"
    await callback.answer(ack)
    await cmd_start(callback.message)

@dp.callback_query(F.data == "btn_stats")
async def cb_stats(callback: types.CallbackQuery):
    await callback.answer()
    await cmd_stats(callback.message)

@dp.callback_query(F.data.startswith("q_"))
async def cb_quick_q(callback: types.CallbackQuery):
    await callback.answer()
    lang = user_languages.get(callback.from_user.id, 'uz')
    q_map = {
        'q_cement': "2024-yilda eng ko'p sement sotgan 5 ta sotuvchini ko'rsating" if lang == 'uz' else "Покажи 5 крупнейших продавцов цемента в 2024 году",
        'q_bk001': "BK001 kodi qaysi brokerga tegishli va uning STIRi nima?" if lang == 'uz' else "Кому принадлежит брокерский код BK001 и какой у него ИНН?",
        'q_cancel': "2023-yilda bekor qilingan bitimlar soni nechta va ularning umumiy summasi qancha bo'lgan?" if lang == 'uz' else "Сколько аннулированных сделок было в 2023 году и на какую сумму?"
    }
    question = q_map.get(callback.data)
    if question:
        await process_query(callback.message, question, lang)

@dp.message(F.text)
async def handle_message(message: types.Message):
    lang = user_languages.get(message.from_user.id, None)
    await process_query(message, message.text, lang)

async def process_query(message: types.Message, query_text: str, lang: str = None):
    # Send typing status
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Process with Agent in executor thread so it doesn't block async loop
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, agent.answer_question, query_text, lang)
    
    answer_text = res['answer']
    
    # Check length for telegram (4096 limit)
    if len(answer_text) <= 4000:
        try:
            await message.answer(answer_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Fallback to plain text if markdown formatting issue
            await message.answer(answer_text)
    else:
        # Split into chunks
        chunks = [answer_text[i:i+3800] for i in range(0, len(answer_text), 3800)]
        for chunk in chunks:
            try:
                await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await message.answer(chunk)

async def main():
    token = TELEGRAM_BOT_TOKEN
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("\n" + "="*70)
        print("⚠️  TELEGRAM_BOT_TOKEN topilmadi!")
        print("Botni ishga tushirish uchun:")
        print("1. @BotFather orqali Telegram bot yarating va TOKEN oling.")
        print("2. .env faylida yoki muhit o'zgaruvchisida TELEGRAM_BOT_TOKEN ni ko'rsating:")
        print("   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
        print("3. Qaytadan 'python run_bot.py' ni ishga tushiring.")
        print("="*70 + "\n")
        return

    bot = Bot(token=token)
    print("🚀 Telegram bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
