import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import google.generativeai as genai

# ===== НАСТРОЙКИ =====
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    print("❌ Ошибка: Токен бота не найден в переменных окружения!")
    sys.exit(1)

GEMINI_API_KEY = "AIzaSyCUiEGek4vMPjtB3gUOs9g5ZVjq9GV_9R8"
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-2.5-flash')

# ===== ПРЕМИУМ ЭМОДЗИ ID =====
EMOJI = {
    "gear": "5870982283724328568",
    "profile": "5870994129244131212",
    "users": "5870772616305839506",
    "user_check": "5891207662678317861",
    "user_x": "5893192487324880883",
    "file": "5870528606328852614",
    "smile": "5870764288364252592",
    "growth": "5870930636742595124",
    "stats": "5870921681735781843",
    "home": "5873147866364514353",
    "lock_closed": "6037249452824072506",
    "lock_open": "6037496202990194718",
    "megaphone": "6039422865189638057",
    "check": "5870633910337015697",
    "cross": "5870657884844462243",
    "pencil": "5870676941614354370",
    "trash": "5870875489362513438",
    "down": "5893057118545646106",
    "clip": "6039451237743595514",
    "link": "5769289093221454192",
    "info": "6028435952299413210",
    "bot": "6030400221232501136",
    "eye": "6037397706505195857",
    "eye_hidden": "6037243349675544634",
    "send": "5963103826075456248",
    "download": "6039802767931871481",
    "bell": "6039486778597970865",
    "gift": "6032644646587338669",
    "clock": "5983150113483134607",
    "party": "6041731551845159060",
    "font": "5870801517140775623",
    "write": "5870753782874246579",
    "media": "6035128606563241721",
    "geo": "6042011682497106307",
    "wallet": "5769126056262898415",
    "box": "5884479287171485878",
    "crypto": "5260752406890711732",
    "calendar": "5890937706803894250",
    "tag": "5886285355279193209",
    "time_past": "5775896410780079073",
    "apps": "5778672437122045013",
    "brush": "6050679691004612757",
    "add_text": "5771851822897566479",
    "format": "5778479949572738874",
    "money": "5904462880941545555",
    "money_send": "5890848474563352982",
    "money_accept": "5879814368572478751",
    "code": "5940433880585605708",
    "loading": "5345906554510012647",
    "back": "5893057118545646106",
    "ask": "5963103826075456248",
    "stop": "5870875489362513438",
    "clear": "5870657884844462243",
}

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ИНИЦИАЛИЗАЦИЯ БОТА =====
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ===== СОСТОЯНИЯ =====
class DialogState(StatesGroup):
    waiting_question = State()

# ===== КЛАВИАТУРЫ =====
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(
            text="❓ Задать вопрос",
            icon_custom_emoji_id=EMOJI["ask"]
        )
    )
    builder.row(
        KeyboardButton(
            text="ℹ О боте",
            icon_custom_emoji_id=EMOJI["info"]
        ),
        KeyboardButton(
            text="❌ Остановить",
            icon_custom_emoji_id=EMOJI["stop"]
        )
    )
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="◁ Отмена",
        callback_data="cancel_dialog",
        icon_custom_emoji_id=EMOJI["back"]
    )
    return builder.as_markup()

def get_after_answer_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Задать ещё вопрос",
            callback_data="ask_again",
            icon_custom_emoji_id=EMOJI["ask"]
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Очистить историю",
            callback_data="clear_history",
            icon_custom_emoji_id=EMOJI["trash"]
        )
    )
    return builder.as_markup()

# ===== КОМАНДЫ =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = f"""
<b><tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> Привет, {message.from_user.full_name}!</b>

Я бот для ответов на любые вопросы.

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <b>Что я умею:</b>
• Отвечать на вопросы
• Помнить контекст диалога

<tg-emoji emoji-id="{EMOJI['write']}">✍</tg-emoji> <b>Как пользоваться:</b>
1. Нажмите <b>«❓ Задать вопрос»</b>
2. Напишите свой вопрос
3. Получите ответ

<tg-emoji emoji-id="{EMOJI['gear']}">⚙</tg-emoji> <b>Команды:</b>
/start — Главное меню
/ask — Задать вопрос
/clear — Очистить историю
/cancel — Отменить диалог

<tg-emoji emoji-id="{EMOJI['smile']}">🙂</tg-emoji> <i>Начните прямо сейчас!</i>
"""
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext):
    await state.set_state(DialogState.waiting_question)
    text = f"""
<tg-emoji emoji-id="{EMOJI['write']}">✍</tg-emoji> <b>Режим вопросов активирован</b>

Напишите ваш вопрос.

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <i>Для отмены нажмите кнопку ниже или /cancel</i>
"""
    await message.answer(text, reply_markup=get_cancel_keyboard())

@dp.message(Command("clear"))
async def cmd_clear(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    
    await state.update_data(history=[])
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>История диалога очищена!</b>

Контекст сброшен.
"""
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            f'<tg-emoji emoji-id="{EMOJI["info"]}">ℹ</tg-emoji> Нет активного диалога.',
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>Диалог отменён</b>

Вы вернулись в главное меню.
"""
    await message.answer(text, reply_markup=get_main_keyboard())

# ===== ОБРАБОТЧИКИ КНОПОК =====
@dp.message(F.text == "❓ Задать вопрос")
async def button_ask(message: Message, state: FSMContext):
    await cmd_ask(message, state)

@dp.message(F.text == "ℹ О боте")
async def button_about(message: Message):
    about_text = f"""
<tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> <b>О боте</b>

<b>Название:</b> Q&A Bot
<b>Версия:</b> 1.0.0

<tg-emoji emoji-id="{EMOJI['code']}">🔨</tg-emoji> <b>Возможности:</b>
• Контекстные диалоги
• Быстрые ответы
• Поддержка русского языка

<tg-emoji emoji-id="{EMOJI['link']}">🔗</tg-emoji> <i>Всегда рад помочь!</i>
"""
    await message.answer(about_text)

@dp.message(F.text == "❌ Остановить")
async def button_stop(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(history=[])
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>Бот остановлен</b>

История очищена.
"""
    await message.answer(text, reply_markup=get_main_keyboard())

# ===== ОБРАБОТЧИКИ ВОПРОСОВ =====
@dp.message(DialogState.waiting_question)
async def process_question(message: Message, state: FSMContext):
    question = message.text
    
    data = await state.get_data()
    history = data.get("history", [])
    
    wait_msg = await message.answer(
        f'<tg-emoji emoji-id="{EMOJI["loading"]}">🔄</tg-emoji> <i>Думаю над ответом...</i>'
    )
    
    try:
        context = "\n".join(history[-6:]) if history else "Нет контекста"
        full_prompt = f"""
Ты — полезный ассистент. Отвечай подробно и по делу на русском языке.

Предыдущий диалог:
{context}

Вопрос: {question}

Ответ:
"""
        
        response = GEMINI_MODEL.generate_content(full_prompt)
        answer = response.text if response.text else "Не удалось сгенерировать ответ."
        
        history.append(f"Вопрос: {question}")
        history.append(f"Ответ: {answer}")
        await state.update_data(history=history)
        
        await wait_msg.delete()
        
        answer_text = f"""
<tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> <b>Ответ:</b>

{answer}
"""
        await message.answer(answer_text, reply_markup=get_after_answer_keyboard())
        
    except Exception as e:
        await wait_msg.delete()
        error_text = f"""
<tg-emoji emoji-id="{EMOJI['cross']}">❌</tg-emoji> <b>Ошибка</b>

<code>{str(e)}</code>
"""
        await message.answer(error_text, reply_markup=get_after_answer_keyboard())

# ===== CALLBACKS =====
@dp.callback_query(F.data == "cancel_dialog")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f'<tg-emoji emoji-id="{EMOJI["check"]}">✅</tg-emoji> <b>Диалог отменён</b>'
    )
    await callback.answer()

@dp.callback_query(F.data == "ask_again")
async def callback_ask_again(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DialogState.waiting_question)
    text = f"""
<tg-emoji emoji-id="{EMOJI['write']}">✍</tg-emoji> <b>Жду ваш вопрос</b>

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <i>Контекст сохранён</i>
"""
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "clear_history")
async def callback_clear_history(callback: CallbackQuery, state: FSMContext):
    await state.update_data(history=[])
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>История очищена!</b>
"""
    await callback.message.edit_text(text)
    await callback.answer()

# ===== ОБРАБОТЧИК ЛЮБЫХ СООБЩЕНИЙ =====
@dp.message()
async def handle_any_message(message: Message):
    text = f"""
<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <b>Вы не в режиме вопросов</b>

Нажмите <b>«❓ Задать вопрос»</b> или /ask
"""
    await message.answer(text, reply_markup=get_main_keyboard())

# ===== ЗАПУСК =====
async def main():
    logger.info("🚀 Запуск бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
