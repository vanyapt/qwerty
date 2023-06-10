from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from data.db import *
from loader import *


async def create_admin_markup(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    admmarkup = InlineKeyboardMarkup()
    adm1 = InlineKeyboardButton(text = await translate_text("Создать публикацию", user_language), callback_data='create_post_select')
    adm2 = InlineKeyboardButton(text = await translate_text("Отложенные", user_language), callback_data='deferred_post')
    adm3 = InlineKeyboardButton(text = await translate_text("Отредактировать", user_language), callback_data='editing_post')
    adm4 = InlineKeyboardButton(text = await translate_text("Администраторы", user_language), callback_data='stats')
    adm5 = InlineKeyboardButton(text = await translate_text("Настройка", user_language), callback_data='options')
    adm7 = InlineKeyboardButton(text = await translate_text("Модерация", user_language), callback_data='moderation')
    admmarkup.add(adm1).add(adm2, adm3).add(adm4, adm5).add(adm7)
    return admmarkup


async def create_sendfile_markup(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    sendfile = InlineKeyboardMarkup()
    send1 = InlineKeyboardButton(text = await translate_text("Добавить URL-кнопки", user_language), callback_data='add_URL')
    send2 = InlineKeyboardButton(text = await translate_text("Удалить сообщение", user_language), callback_data='delete_message')
    sendfile.add(send1).add(send2)
    return sendfile


async def create_channelsend_markup(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    channelsend = InlineKeyboardMarkup()
    sp1 = InlineKeyboardButton(text = await translate_text("Опубликовать", user_language), callback_data='send_post')
    sp2 = InlineKeyboardButton(text = await translate_text("Отложить", user_language), callback_data='later_post')
    text3 = "« " + await translate_text("Назад", user_language)
    sp3 = InlineKeyboardButton(text = text3, callback_data='back_Post')
    channelsend.add(sp1, sp2).add(sp3)
    return channelsend


# Публикация меню в чате
async def create_sendpostnext_markup(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    sendPostnext = InlineKeyboardMarkup()
    sn1 = InlineKeyboardButton(text = await translate_text("Опубликовать сейчас", user_language), callback_data='next_send_post')
    text = "« " + await translate_text("Назад", user_language)
    sn2 = InlineKeyboardButton(text = await translate_text(text, user_language), callback_data='back_next_post')
    sendPostnext.add(sn1, sn2)
    return sendPostnext


# Панель файл
async def create_panelsend_markup(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    panelsend = ReplyKeyboardMarkup(resize_keyboard=True)
    panelsend_moder = ReplyKeyboardMarkup(resize_keyboard=True)
    pl1 =  KeyboardButton(text=await translate_text("Очистить", user_language))
    pl2 =  KeyboardButton(text=await translate_text("Предпросмотр", user_language))
    pl3 =  KeyboardButton(text=await translate_text("Отменить", user_language))
    pl4 =  KeyboardButton(text=await translate_text("Далее", user_language))
    panelsend.add(pl1, pl2).add(pl3, pl4)
    panelsend_moder.add(pl3)
    return panelsend, panelsend_moder




# Удаление добавленных ссылок
async def create_keyboard_markup(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    keyboard = InlineKeyboardMarkup(row_width=1)
    send5 = InlineKeyboardButton(text = await translate_text("Удалить URL-кнопки", user_language), callback_data='delete_URL')
    send6 = InlineKeyboardButton(text = await translate_text("Удалить сообщение", user_language), callback_data='delete_message')
    keyboard.add(send5, send6)
    return keyboard



# Основа отложить
async def create_keyboard_laterkey(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    b =  "« " + await translate_text("Назад", user_language)
    lt3 = InlineKeyboardButton(text = b, callback_data='back_next_post')
    laterkey = InlineKeyboardMarkup()
    laterkey.row(lt3)
    return laterkey

async def create_keyboard_cancel_url(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    cancel_url=ReplyKeyboardMarkup(resize_keyboard=True)
    text1=await translate_text("Отмена", user_language)
    cu1 = KeyboardButton(text=text1)
    cancel_url.add(cu1)
    return cancel_url

async def create_keyboard_super_admin(user_id):
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    super_menu = InlineKeyboardMarkup()
    list_back = InlineKeyboardMarkup()
    list_null = InlineKeyboardMarkup()
    list_nullsup = InlineKeyboardMarkup()
    b =  "« " + await translate_text("Назад", user_language)
    sm1 = InlineKeyboardButton(text = await translate_text("Список групп", user_language), callback_data='list_groups')
    sm2 = InlineKeyboardButton(text = await translate_text("Добавить группу", user_language), callback_data='add_channel')
    sm3 = InlineKeyboardButton(text = await translate_text("Удалить группу", user_language), callback_data='delete_channel')
    sm4 = InlineKeyboardButton(text = b, callback_data='back_menu')
    sm5 = InlineKeyboardButton(text = await translate_text("Активность", user_language), callback_data='stats_bot')
    super_menu.add(sm1, sm5).add(sm2, sm3)
    list_back.add(sm4)
    list_null.add(sm2)
    list_nullsup.add(sm2).add(sm4)
    return list_back, super_menu, list_nullsup, list_null


home_menu = InlineKeyboardMarkup()
home_menu1 = InlineKeyboardMarkup()
home = InlineKeyboardButton(text = "« Назад", callback_data='home_menu')
home1 = InlineKeyboardButton(text = "« Назад", callback_data='home_menu_reduct')
home_menu.add(home)
home_menu1.add(home1)


reduct_message = InlineKeyboardMarkup()
reduct_message_url = InlineKeyboardMarkup()
r1 = InlineKeyboardButton(text = "Изменить URL-кнопки", callback_data='mess_reduct_URL')
r2 = InlineKeyboardButton(text = "Удалить URL-кнопки", callback_data='mess_delete_URL')
r3 = InlineKeyboardButton(text = "Сохранить изменения", callback_data='save_reduct')
r4 = InlineKeyboardButton(text = "Выйти из редактирования", callback_data='exit_reduct')
r5 = InlineKeyboardButton(text = "Добавить URL-кнопки", callback_data='add_new_URL')
reduct_message.add(r5).add(r3).add(r4)
reduct_message_url.add(r1).add(r2).add(r3).add(r4)



d1 = InlineKeyboardButton(text = "Изменить время", callback_data='change_time')
d2 = InlineKeyboardButton(text = "Удалить пост", callback_data='delete_public')
d3 = InlineKeyboardButton(text = "« Назад", callback_data='back_list_public')
