from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

keystart = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
bs1 = KeyboardButton(text="")
bs2 = KeyboardButton(text="")
bs3 = KeyboardButton(text="")
keystart.add(bs1).add(bs2, bs3)
