from loader import *
from config import *


async def set_default_command(dp, chat_id: int, user_language: str):
    commands = [
        types.BotCommand(command="start", description=await translate_text("Начать работать", user_language)),
        types.BotCommand(command="support", description=await translate_text("Написать в техподдержку", user_language)),
        types.BotCommand(command='language', description=await translate_text('Языки en, uk, ru', user_language))
    ]
    await bot.set_my_commands(commands, scope=types.BotCommandScopeChat(chat_id))


async def set_start_admin(dp, chat_id: int, user_id: int, user_language: str):
    commands = [
        types.BotCommand(command='start', description=await translate_text('Начало работы', user_language)),
        types.BotCommand(command='admin', description=await translate_text('Админ панель', user_language)),
        types.BotCommand(command='language', description=await translate_text('Языки en, uk, ru', user_language))
    ]
    if user_id in get_admins():
        commands.append(types.BotCommand(command='superadmin', description=await translate_text('Добавить / Удалить группу', user_language)))
    await bot.set_my_commands(commands, scope = types.BotCommandScopeChat(chat_id))


async def publish_post(id_post, publish_time):
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    try:
        await cursor.execute("SELECT file, file_type, text, url_buttons, id_group FROM my_post WHERE id_post=?", (id_post,))
        result = await cursor.fetchone()
        if result is None:
            print(f"Post {id_post} does not exist.")
            return
        file, file_type, text, url_buttons, group_id = result

        delay = (publish_time - datetime.now()).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)

        await cursor.execute("DELETE FROM my_post WHERE id_post = ?", (id_post,))
        await conn.commit()

        if file_type == 'photo':
            await bot.send_photo(chat_id=group_id, photo=file, caption=text, reply_markup=url_buttons if url_buttons else None)
        elif file_type == 'video':
            await bot.send_video(chat_id=group_id, video=file, caption=text, reply_markup=url_buttons if url_buttons else None)
        elif file_type == 'gif':
            await bot.send_animation(chat_id=group_id, animation=file, caption=text, reply_markup=url_buttons if url_buttons else None)
        elif file_type == 'document':
            await bot.send_document(chat_id=group_id, document=file, caption=text, reply_markup=url_buttons if url_buttons else None)
        elif file_type == 'text':
            await bot.send_message(chat_id=group_id, text=text, reply_markup=url_buttons if url_buttons else None)
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()


async def he(link: types.ChatJoinRequest):
    await bot.approve_chat_join_request(link.chat.id, link.from_user.id)


async def callback_options(call: types.CallbackQuery):
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM setting WHERE id_admin = ?", (call.from_user.id,))
    existing_row = cursor.fetchone()
    if existing_row is None:
        cursor.execute("INSERT INTO setting (id_admin, disable_web_page_preview, disable_notification) VALUES (?, ?, ?)",
                       (call.from_user.id, False, True))
        conn.commit()

    cursor.close()
    conn.close()

    await update_menu(call)


async def update_setting(call: types.CallbackQuery, column: str, value):
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE setting SET {column} = ? WHERE id_admin = ?", (value, call.from_user.id))
    conn.commit()
    cursor.close()
    conn.close()


async def update_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    with sq.connect('my_db.db') as conn:
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    cursor.execute("SELECT disable_notification, disable_web_page_preview FROM setting WHERE id_admin = ?", (call.from_user.id,))
    existing_row = cursor.fetchone()
    disable_notification, disable_web_page_preview = existing_row
    s_1 = await translate_text("Звуковое уведомление", user_language)
    p_1 = await translate_text("Предпросмотр ссылок", user_language)
    b_b = "« " + await translate_text("Назад", user_language)
    on = await translate_text("Включено.", user_language)
    off = await translate_text("Выключено.", user_language)
    o = await translate_text("Вкл.", user_language)
    f = await translate_text("Выкл.", user_language)
    s = InlineKeyboardButton(text = f"{s_1}: { f if disable_notification else o }", callback_data = "sound")
    p = InlineKeyboardButton(text = f"{p_1}: { f if disable_web_page_preview else o }", callback_data = "preview")
    b_back = InlineKeyboardButton(text = b_b, callback_data = "home_menu_reduct")
    key_setting = InlineKeyboardMarkup(row_width=1)
    key_setting.add(s, p, b_back)
    set = await translate_text("Текущие настройки", user_language)
    settings_status_message = f"{set}:\n\n" \
                              f"{s_1}: <b>{ on if not disable_notification else off }</b>\n" \
                              f"{p_1}: <b>{ on if not disable_web_page_preview else off }</b>"

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=settings_status_message, reply_markup=key_setting)


async def callback_options_sound(call: types.CallbackQuery):
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT disable_notification FROM setting WHERE id_admin = ?", (call.from_user.id,))
    existing_row = cursor.fetchone()
    if existing_row:
        disable_notification = existing_row[0]
        await update_setting(call, 'disable_notification', not disable_notification)
    await update_menu(call)


async def callback_options_preview(call: types.CallbackQuery):
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT disable_web_page_preview FROM setting WHERE id_admin = ?", (call.from_user.id,))
    existing_row = cursor.fetchone()
    if existing_row:
        disable_web_page_preview = existing_row[0]
        await update_setting(call, 'disable_web_page_preview', not disable_web_page_preview)
    await update_menu(call)


def register_handlers_other(dp: Dispatcher):
    dp.register_chat_join_request_handler(he)
    dp.register_callback_query_handler(callback_options, text='options', state='*')
    dp.register_callback_query_handler(callback_options_sound, text="sound", state="*")
    dp.register_callback_query_handler(callback_options_preview, text="preview", state="*")
