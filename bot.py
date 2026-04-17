import asyncio
import logging
import os
import sys
from typing import Optional

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
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')

# ===== ПРЕМИУМ ЭМОДЗИ ID =====
EMOJI = {
    "gear": "5870982283724328568",           # ⚙ Настройки
    "profile": "5870994129244131212",         # 👤 Профиль
    "users": "5870772616305839506",           # 👥 Люди
    "user_check": "5891207662678317861",      # 👤 Человек и галочка
    "user_x": "5893192487324880883",          # 👤 Человек и крестик
    "file": "5870528606328852614",            # 📁 Файл
    "smile": "5870764288364252592",           # 🙂 Смайл улыбка
    "growth": "5870930636742595124",          # 📊 Рост график
    "stats": "5870921681735781843",           # 📊 Статистика график
    "home": "5873147866364514353",            # 🏘 Дом
    "lock_closed": "6037249452824072506",     # 🔒 Замок закрытый
    "lock_open": "6037496202990194718",       # 🔓 Замок открытый
    "megaphone": "6039422865189638057",       # 📣 Рупор
    "check": "5870633910337015697",           # ✅ Галочка
    "cross": "5870657884844462243",           # ❌ Крестик
    "pencil": "5870676941614354370",          # 🖋 Карандаш
    "trash": "5870875489362513438",           # 🗑 Мусорный бак
    "down": "5893057118545646106",            # 📰 Вниз
    "clip": "6039451237743595514",            # 📎 Скрепка
    "link": "5769289093221454192",            # 🔗 Ссылка
    "info": "6028435952299413210",            # ℹ Инфо
    "bot": "6030400221232501136",             # 🤖 Бот
    "eye": "6037397706505195857",             # 👁 Глаз
    "eye_hidden": "6037243349675544634",      # 👁 Скрыто
    "send": "5963103826075456248",            # ⬆ Отправить
    "download": "6039802767931871481",        # ⬇ Скачать
    "bell": "6039486778597970865",            # 🔔 Уведомление
    "gift": "6032644646587338669",            # 🎁 Подарок
    "clock": "5983150113483134607",           # ⏰ Часы
    "party": "6041731551845159060",           # 🎉 Ура
    "font": "5870801517140775623",            # 🔗 Шрифт
    "write": "5870753782874246579",           # ✍ Писать
    "media": "6035128606563241721",           # 🖼 Медиа фото
    "geo": "6042011682497106307",             # 📍 Геометка
    "wallet": "5769126056262898415",          # 👛 Кошелек
    "box": "5884479287171485878",             # 📦 Коробка
    "crypto": "5260752406890711732",          # 👾 Криптобот
    "calendar": "5890937706803894250",        # 📅 Календарь
    "tag": "5886285355279193209",             # 🏷 Бирка
    "time_past": "5775896410780079073",       # 🕓 Время прошло
    "apps": "5778672437122045013",            # 📦 Приложения
    "brush": "6050679691004612757",           # 🖌 Кисточка
    "add_text": "5771851822897566479",        # 🔡 Добавить текст
    "format": "5778479949572738874",          # ↔ Разрешение/формат
    "money": "5904462880941545555",           # 🪙 Деньги
    "money_send": "5890848474563352982",      # 🪙 Отправить деньги
    "money_accept": "5879814368572478751",    # 🏧 Принять деньги
    "code": "5940433880585605708",            # 🔨 Код </>
    "loading": "5345906554510012647",         # 🔄 Загрузка
    "back": "5893057118545646106",            # ◁ Назад
    "ask": "5963103826075456248",             # ⬆ Отправить (для вопросов)
    "stop": "5870875489362513438",            # 🗑 Стоп
    "clear": "5870657884844462243",           # ❌ Очистить
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
    """Основная клавиатура бота"""
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
    """Клавиатура для отмены диалога"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="◁ Отмена",
        callback_data="cancel_dialog",
        icon_custom_emoji_id=EMOJI["back"]
    )
    return builder.as_markup()

def get_after_answer_keyboard():
    """Клавиатура после получения ответа"""
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
    """Обработчик команды /start"""
    welcome_text = f"""
<b><tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> Привет, {message.from_user.full_name}!</b>

Я бот для ответов на вопросы с использованием <b>Gemini AI</b>.

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <b>Что я умею:</b>
• Отвечать на любые вопросы
• Помнить контекст диалога
• Использовать красивый премиум-дизайн

<tg-emoji emoji-id="{EMOJI['write']}">✍</tg-emoji> <b>Как пользоваться:</b>
1. Нажмите <b>«❓ Задать вопрос»</b>
2. Напишите свой вопрос
3. Получите развёрнутый ответ

<tg-emoji emoji-id="{EMOJI['gear']}">⚙</tg-emoji> <b>Доступные команды:</b>
/start — Главное меню
/ask — Задать вопрос
/clear — Очистить историю
/cancel — Отменить текущий диалог

<tg-emoji emoji-id="{EMOJI['smile']}">🙂</tg-emoji> <i>Начните прямо сейчас!</i>
"""
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext):
    """Обработчик команды /ask"""
    await state.set_state(DialogState.waiting_question)
    text = f"""
<tg-emoji emoji-id="{EMOJI['write']}">✍</tg-emoji> <b>Режим вопросов активирован</b>

Напишите ваш вопрос, и я отвечу с помощью <b>Gemini AI</b>.

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <i>Для отмены нажмите кнопку ниже или используйте /cancel</i>
"""
    await message.answer(text, reply_markup=get_cancel_keyboard())

@dp.message(Command("clear"))
async def cmd_clear(message: Message, state: FSMContext):
    """Обработчик команды /clear"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    
    await state.update_data(history=[])
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>История диалога очищена!</b>

Контекст сброшен, можете начинать новый разговор.
"""
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработчик команды /cancel"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            f'<tg-emoji emoji-id="{EMOJI["info"]}">ℹ</tg-emoji> Нет активного диалога для отмены.',
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>Диалог отменён</b>

Вы вернулись в главное меню.
"""
    await message.answer(text, reply_markup=get_main_keyboard())

# ===== ОБРАБОТЧИКИ КНОПОК КЛАВИАТУРЫ =====
@dp.message(F.text == "❓ Задать вопрос")
async def button_ask(message: Message, state: FSMContext):
    """Обработчик кнопки 'Задать вопрос'"""
    await cmd_ask(message, state)

@dp.message(F.text == "ℹ О боте")
async def button_about(message: Message):
    """Обработчик кнопки 'О боте'"""
    about_text = f"""
<tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> <b>О боте</b>

<b>Название:</b> Gemini Q&A Bot
<b>Версия:</b> 1.0.0
<b>Модель:</b> Gemini 1.5 Flash

<tg-emoji emoji-id="{EMOJI['code']}">🔨</tg-emoji> <b>Возможности:</b>
• Контекстные диалоги с памятью
• Быстрые ответы на любые вопросы
• Поддержка русского языка
• Премиум-дизайн интерфейса

<tg-emoji emoji-id="{EMOJI['gear']}">⚙</tg-emoji> <b>Технологии:</b>
• Aiogram 3.x
• Google Gemini API
• FSM для состояний

<tg-emoji emoji-id="{EMOJI['link']}">🔗</tg-emoji> <i>Создан для демонстрации возможностей</i>
"""
    await message.answer(about_text)

@dp.message(F.text == "❌ Остановить")
async def button_stop(message: Message, state: FSMContext):
    """Обработчик кнопки 'Остановить'"""
    await state.clear()
    await state.update_data(history=[])
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>Бот остановлен</b>

История очищена, все диалоги завершены.
"""
    await message.answer(text, reply_markup=get_main_keyboard())

# ===== ОБРАБОТЧИКИ ВОПРОСОВ =====
@dp.message(DialogState.waiting_question)
async def process_question(message: Message, state: FSMContext):
    """Обработка вопроса от пользователя"""
    question = message.text
    
    # Получаем историю из состояния
    data = await state.get_data()
    history = data.get("history", [])
    
    # Отправляем сообщение о начале генерации
    wait_msg = await message.answer(
        f'<tg-emoji emoji-id="{EMOJI["loading"]}">🔄</tg-emoji> <i>Генерирую ответ...</i>'
    )
    
    try:
        # Формируем контекст для Gemini
        context = "\n".join(history[-6:]) if history else "Нет предыдущего контекста"
        full_prompt = f"""
Ты — полезный и дружелюбный ассистент в Telegram. Отвечай на вопросы подробно, но по делу.
Используй русский язык. Будь вежлив и информативен.

Предыдущий контекст диалога:
{context}

Текущий вопрос пользователя: {question}

Твой ответ (только текст ответа, без дополнительных комментариев):
"""
        
        # Получаем ответ от Gemini
        response = GEMINI_MODEL.generate_content(full_prompt)
        answer = response.text if response.text else "Извините, не удалось сгенерировать ответ."
        
        # Обновляем историю
        history.append(f"Вопрос: {question}")
        history.append(f"Ответ: {answer}")
        await state.update_data(history=history)
        
        # Удаляем сообщение ожидания
        await wait_msg.delete()
        
        # Отправляем ответ
        answer_text = f"""
<tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> <b>Ответ Gemini:</b>

{answer}

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <i>Использована модель: Gemini 1.5 Flash</i>
"""
        await message.answer(answer_text, reply_markup=get_after_answer_keyboard())
        
    except Exception as e:
        await wait_msg.delete()
        error_text = f"""
<tg-emoji emoji-id="{EMOJI['cross']}">❌</tg-emoji> <b>Ошибка при генерации ответа</b>

<code>{str(e)}</code>

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <i>Попробуйте позже или задайте другой вопрос.</i>
"""
        await message.answer(error_text, reply_markup=get_after_answer_keyboard())

# ===== ОБРАБОТЧИКИ CALLBACK =====
@dp.callback_query(F.data == "cancel_dialog")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена диалога через инлайн-кнопку"""
    await state.clear()
    await callback.message.edit_text(
        f'<tg-emoji emoji-id="{EMOJI["check"]}">✅</tg-emoji> <b>Диалог отменён</b>'
    )
    await callback.answer("Диалог завершён")

@dp.callback_query(F.data == "ask_again")
async def callback_ask_again(callback: CallbackQuery, state: FSMContext):
    """Задать ещё вопрос"""
    await state.set_state(DialogState.waiting_question)
    text = f"""
<tg-emoji emoji-id="{EMOJI['write']}">✍</tg-emoji> <b>Жду ваш следующий вопрос</b>

<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <i>Контекст предыдущего диалога сохранён</i>
"""
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "clear_history")
async def callback_clear_history(callback: CallbackQuery, state: FSMContext):
    """Очистка истории диалога"""
    await state.update_data(history=[])
    text = f"""
<tg-emoji emoji-id="{EMOJI['check']}">✅</tg-emoji> <b>История диалога очищена!</b>

Можете задать новый вопрос.
"""
    await callback.message.edit_text(text)
    await callback.answer("История очищена")

# ===== ОБРАБОТЧИК ЛЮБЫХ СООБЩЕНИЙ (ВНЕ ДИАЛОГА) =====
@dp.message()
async def handle_any_message(message: Message):
    """Обработчик любых сообщений вне режима диалога"""
    text = f"""
<tg-emoji emoji-id="{EMOJI['info']}">ℹ</tg-emoji> <b>Вы не в режиме вопросов</b>

Чтобы задать вопрос, нажмите кнопку <b>«❓ Задать вопрос»</b> или используйте команду /ask

<tg-emoji emoji-id="{EMOJI['bot']}">🤖</tg-emoji> <i>Я готов помочь вам найти ответы!</i>
"""
    await message.answer(text, reply_markup=get_main_keyboard())

# ===== ЗАПУСК БОТА =====
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
