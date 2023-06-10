import logging
import pytz
import asyncio
import calendar
import math
import re
import copy
import sqlite3 as sq
import aiosqlite
from aiogram import types
from io import BytesIO
from matplotlib.dates import DateFormatter
from dateutil.relativedelta import relativedelta
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ContentType, Message, CallbackQuery
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher.middlewares import BaseMiddleware
from datetime import datetime, timedelta
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime, time
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime, time


from PIL import Image, ImageDraw, ImageFont
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import ChatIdIsEmpty, ChatNotFound, BotBlocked, MessageNotModified, MessageToDeleteNotFound, MessageCantBeEdited
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaAnimation, InputMediaDocument
import matplotlib.ticker as ticker
import numpy as np


from googletrans import Translator
from telegram import Update


from config import token


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=token, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)
time_set = pytz.timezone('Europe/Kiev')


class state_user_lang(StatesGroup):
    lang = State()


def static_translation(text, lang):
    if lang in translations and text in translations[lang]:
        return translations[lang][text]
    return None


async def translate_text(text, user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,)).fetchone()
        if user_id is None:
            dest_language = 'uk'
        elif user_id == 'ru':
            return text
        else:
            dest_language = user_id

        static_trans = static_translation(text, dest_language)
        if static_trans is not None:
            return static_trans

    translator = Translator()
    translation = translator.translate(text, dest=dest_language)
    return translation.text


LANGDICT = {
    'en': 'English',
    'ru': 'Русский',
    'uk': 'Українська'
}


translations = {
        'en': {
            'Предпросмотр': 'Preview',
            'Настройка': 'Settings',
            'Далее': 'Next',
            'Отмена': 'Cancell',
            'Админ панель': 'Admin panel',
            'Добавить URL-кнопки': 'Add URL-buttons',
            'Удалить URL-кнопки': 'Remove URL-buttons',
            'Удалить сообщение': 'Delete message',
            'Чат не найден': 'Chat unknown',
            'Включено.': 'Included',
            'Выключено.': 'Turned off.',
            'Вкл.': 'On',
            'Выкл.': 'Off',
        },
        'uk': {
            'Предпросмотр': 'Попередній перегляд',
            'Настройка': 'Налаштування',
            'Далее': 'Далі',
            'Очистить': 'Очистити',
            'Админ панель': 'Адмін панель',
            'Добавить URL-кнопки': 'Додати URL-кнопки',
            'Удалить URL-кнопки': 'Видалити URL-кнопки',
            'Удалить сообщение': 'Видалити повідомлення',
            'Чат не найден': 'Чат не знайдено',
            'Включено.': 'Увімкнено',
            'Выключено.': 'Вимкнено',
            'Вкл.': 'Увімк',
            'Выкл.': 'Вимк',
            'Список групп': 'Список груп',
        }
    }
