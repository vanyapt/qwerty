from loader import *
from config import *
from data.db import create_db, setting_admin
from buttons.admin_kb import *


class sendStates(StatesGroup):
    photo = State()
    video = State()
    text = State()
    gif = State()
    document = State()
    url_buttons = State()


class sendStatesTime(StatesGroup):
    waiting_time_today = State()
    publish_time = State()


class reductPost(StatesGroup):
    reductstarted = State()
    reduct = State()
    message_id = State()


class ChangeTimeStates(StatesGroup):
    new_time = State()
    post_id = State()


class StatesAdmin(StatesGroup):
    ADMIN_GROUP_SELECTION = State()


async def get_user_settings(user_id):
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='setting'")
    if cursor.fetchone() is None:
        return True, False
    cursor.execute("SELECT disable_web_page_preview, disable_notification FROM setting WHERE id_admin = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        return True, False
    disable_web_page_preview, disable_notification = row
    conn.close()
    return disable_web_page_preview, disable_notification

conn = sq.connect('my_db.db')
cursor = conn.cursor()

#-------------------------------|/start - меню(публикация)|----------------------------------

async def main_menu_list(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await cmd_start_admin(call.message, state)

async def cmd_start_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await create_db()
    await setting_admin()
    list_groups_all = InlineKeyboardMarkup()
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_group, id_admin FROM my_group")
        id_groups_admins = cursor.fetchall()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        if user_language_db is None:
            user_language = 'uk'
        else:
            user_language = user_language_db[0]
        valid_groups = []
        for group_id, id_admin in id_groups_admins:
            try:
                chat_member = await bot.get_chat_member(group_id, message.from_user.id)
                if chat_member.status == 'administrator' or chat_member.status == 'creator' or message.from_user.id in get_admins():
                    admin_ids = id_admin.split(", ")
                    if str(message.from_user.id) in admin_ids:
                        valid_groups.append(group_id)
            except:
                pass
        list_back, super_menu, list_nullsup, list_null = await create_keyboard_super_admin(user_id)
        if len(valid_groups) == 0:
            if message.from_user.id in get_admins():
                message_text = await translate_text('Вы не являетесь администратором ни в одной из групп.', user_language)
                await bot.send_message(message.chat.id, message_text, reply_markup=list_null)
                return
            else:
                return

        for i in range(0, len(valid_groups), 2):
            row = []
            for group_id in valid_groups[i:i+2]:
                group_chat = await bot.get_chat(group_id)
                button_text = group_chat.title
                button_callback_data = f'group_{group_id}'
                row.append(InlineKeyboardButton(text=button_text, callback_data=button_callback_data))
            list_groups_all.row(*row)

        await state.set_state(StatesAdmin.ADMIN_GROUP_SELECTION)
        message_text = await translate_text('Выберите канал, в который вы хотите создать публикацию.', user_language)
        await bot.send_message(message.chat.id, message_text, reply_markup=list_groups_all)
        await state.update_data(group_id=group_id)
    except sq.ProgrammingError as err:
        if str(err) == 'Cannot operate on a closed cursor.':
            cursor = conn.cursor()
            return await cmd_start_admin(message, state)
        raise err


async def process_group_selection(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    await state.finish()
    data = await state.get_data()
    group_id = call.data.split('_')[1]
    if data.get("group_id") == group_id:
        text = await translate_text("Вы уже выбрали эту группу!", user_language)
        await bot.answer_callback_query(callback_query_id=call.id, text=text)
        return

    await state.update_data(group_id=group_id)
    name_group = (await bot.get_chat(group_id)).title

    text_admin = await translate_text('<b>Добро пожаловать в Админ-Панель!</b> \nЗдесь вы можете создавать создать публикации, просматривать статистику канала', user_language) + f' «<b>{name_group}</b>».'
    admmarkup = await create_admin_markup(user_id)
    await call.message.edit_text(text_admin, reply_markup=admmarkup)


async def cancel_post_now(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    data = await state.get_data()
    group_id = data.get("group_id")
    cursor.execute("SELECT id_admin FROM my_group WHERE id_group=?", (group_id,))
    result = cursor.fetchone()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    if result is not None:
        admin_ids = result[0].split(", ")
        if str(message.from_user.id) in admin_ids:
            current_state = await state.get_state()
            text = await translate_text("Отменено.", user_language)
            await bot.send_message(user_id, text, reply_markup=ReplyKeyboardRemove())
            await message.delete()
            await cmd_start_admin(message, state)
            if current_state is None:
                return
            logging.info('Cancelling state %r', current_state)


async def cancel_all(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    user_id = message.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    text = f'{await translate_text("Процес отменен. Все данные стерты. Что бы начать все с начала нажми", user_language)} /admin'
    await message.reply(text, reply_markup=types.ReplyKeyboardRemove())
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)
    await state.finish()


async def cancel1_post(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    data = await state.get_data()
    group_id = data.get("group_id")
    cursor.execute("SELECT id_admin FROM my_group WHERE id_group=?", (group_id,))
    result = cursor.fetchone()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    sendfile = await create_sendfile_markup(user_id)
    panelsend, panelsend_moder = await create_panelsend_markup(user_id)
    if result is not None:
        admin_ids = result[0].split(", ")
        if str(message.from_user.id) in admin_ids:
            async with state.proxy() as data:
                te = await translate_text("Продолжайте отправлять сообщения.", user_language)
                await bot.send_message(message.chat.id, te, reply_markup=panelsend)
                if 'photo' in data:
                    await bot.send_photo(chat_id=message.chat.id, photo=data['photo'], caption=data['text'], reply_markup=sendfile)
                elif 'video' in data:
                    await bot.send_video(chat_id=message.chat.id, video=data['video'], caption=data['text'], reply_markup=sendfile)
                elif 'gif' in data:
                    await bot.send_video(chat_id=message.chat.id, video=data['gif'], caption=data['text'], reply_markup=sendfile)
                elif 'document' in data:
                    await bot.send_video(chat_id=message.chat.id, video=data['document'], caption=data['text'], reply_markup=sendfile)
                elif 'text' in data:
                    await bot.send_message(chat_id=message.chat.id, text=data['text'], reply_markup=sendfile)
            await message.delete()


async def clear_post(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    data = await state.get_data()
    group_id = data.get("group_id")
    cursor.execute("SELECT id_admin FROM my_group WHERE id_group=?", (group_id,))
    result = cursor.fetchone()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    if result is not None:
        admin_ids = result[0].split(", ")
        if str(message.from_user.id) in admin_ids:
            await message.delete()
            await state.finish()
            text = await translate_text("Сообщения удалены.", user_language)
            await bot.send_message(user_id, text)
            await StatesAdmin.ADMIN_GROUP_SELECTION.set()
            await state.update_data({'group_id': group_id})
            await sendStates.video.set()
            await sendStates.text.set()
            await sendStates.photo.set()
            await sendStates.gif.set()
            await sendStates.document.set()


async def preview_post(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    with sq.connect('my_db.db') as conn:
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    async with state.proxy() as data:
        if 'photo' not in data and 'video' not in data and 'text' not in data and 'gif' not in data and 'document' not in data:
            not_file = await translate_text("Нет сообщений для предпросмотра.", user_language)
            await bot.send_message(user_id, not_file)
            await message.delete()
            return
    data = await state.get_data()
    group_id = data.get("group_id")
    cursor.execute("SELECT id_admin FROM my_group WHERE id_group=?", (group_id,))
    result = cursor.fetchone()
    sendfile = await create_sendfile_markup(user_id)
    if result is not None:
        admin_ids = result[0].split(", ")
        if str(message.from_user.id) in admin_ids:
            keyboard = data.get("url_buttons")
            send3 = InlineKeyboardButton(text = await translate_text("Удалить URL-кнопки", user_language), callback_data='delete_URL')
            send4 = InlineKeyboardButton(text = await translate_text("Удалить сообщение", user_language), callback_data='delete_message')

            if keyboard is None:
                keyboard = InlineKeyboardMarkup()

            keyboard.add(send3)
            keyboard.add(send4)

            if 'photo' in data:
                textp = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                        f'{await translate_text("В публикации", user_language)}:\n' \
                        f'1. 📷 {await translate_text("Фото", user_language)}\n' \
                        f'2. ⌨️ {await translate_text("Кнопки", user_language)}'

                if 'url_buttons' in data:
                    await bot.send_photo(chat_id=user_id, photo=data['photo'], caption=data['text'], reply_markup=keyboard)
                    await bot.send_message(chat_id=user_id, text=textp)
                else:
                    textpb = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                            f'{await translate_text("В публикации", user_language)}:\n' \
                            f'1. 📷 {await translate_text("Фото", user_language)}'
                    await bot.send_photo(chat_id=user_id, photo=data['photo'], caption=data['text'], reply_markup=sendfile)
                    await bot.send_message(chat_id=user_id, text=textpb)

            elif 'video' in data:
                textv = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                        f'{await translate_text("В публикации", user_language)}:\n' \
                        f'1. 📹 {await translate_text("Видео", user_language)}\n' \
                        f'2. ⌨️ {await translate_text("Кнопки", user_language)}'

                if 'url_buttons' in data:
                    await bot.send_video(chat_id=user_id, video=data['video'], caption=data['text'], reply_markup=keyboard)
                    await bot.send_message(chat_id=user_id, text=textv)
                else:
                    textvb = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                            f'{await translate_text("В публикации", user_language)}:\n' \
                            f'1. 📹 {await translate_text("Видео", user_language)}'
                    await bot.send_video(chat_id=user_id, video=data['video'], caption=data['text'], reply_markup=sendfile)
                    await bot.send_message(chat_id=user_id, text=textvb)

            elif 'gif' in data:
                textg = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                        f'{await translate_text("В публикации", user_language)}:\n' \
                        f'1. 🎞 {await translate_text("Анимация", user_language)}\n' \
                        f'2. ⌨️ {await translate_text("Кнопки", user_language)}'

                if 'url_buttons' in data:
                    await bot.send_animation(chat_id=user_id, animation=data['gif'], caption=data['text'], reply_markup=keyboard)
                    await bot.send_message(chat_id=user_id, text=textg)
                else:
                    textgb = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                            f'{await translate_text("В публикации", user_language)}:\n' \
                            f'1. 🎞 {await translate_text("Анимация", user_language)}'
                    await bot.send_animation(chat_id=user_id, animation=data['gif'], caption=data['text'], reply_markup=sendfile)
                    await bot.send_message(chat_id=user_id, text=textgb)

            elif 'document' in data:
                textd = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                        f'{await translate_text("В публикации", user_language)}:\n' \
                        f'1. 📄 {await translate_text("Документ", user_language)}\n' \
                        f'2. ⌨️ {await translate_text("Кнопки", user_language)}'

                if 'url_buttons' in data:
                    await bot.send_document(chat_id=user_id, document=data['document'], caption=data['text'], reply_markup=keyboard)
                    await bot.send_message(chat_id=user_id, text=textd)
                else:
                    textdb = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                            f'{await translate_text("В публикации", user_language)}:\n' \
                            f'1. 📄 {await translate_text("Документ", user_language)}'
                    await bot.send_document(chat_id=user_id, document=data['document'], caption=data['text'], reply_markup=sendfile)
                    await bot.send_message(chat_id=user_id, text=textdb)

            elif 'text' in data:
                textt = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                        f'{await translate_text("В публикации", user_language)}:\n' \
                        f'1. 📃 {await translate_text("Текст", user_language)}\n' \
                        f'2. ⌨️ {await translate_text("Кнопки", user_language)}'

                if 'url_buttons' in data:
                    await bot.send_message(chat_id=user_id,text=data['text'], reply_markup=keyboard)
                    await bot.send_message(chat_id=user_id, text=textt)
                else:
                    texttb = f'{await translate_text("Сообщения для предпросмотра отправлены", user_language)}.\n' \
                            f'{await translate_text("В публикации", user_language)}:\n' \
                            f'1. 📃 {await translate_text("Текст", user_language)}'
                    await bot.send_message(chat_id=user_id, text=data['text'], reply_markup=sendfile)
                    await bot.send_message(chat_id=user_id, text=texttb)
        await message.delete()


async def next_post(message: Message, state: FSMContext):
    user_id = message.from_user.id
    channelsend = await create_channelsend_markup(user_id)
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    data = await state.get_data()
    group_id = data.get("group_id")
    cursor.execute("SELECT id_admin FROM my_group WHERE id_group=?", (group_id,))
    result = cursor.fetchone()
    if result is not None:
        admin_ids = result[0].split(", ")
        if str(user_id) in admin_ids:
            try:
                await message.delete()
                data = await state.get_data()
                group_id = data.get("group_id")
                with sq.connect('my_db.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
                    user_language_db = cursor.fetchone()
                    user_language = user_language_db[0]
                name_group = await bot.get_chat(group_id)
                public_mess = await translate_text(f"Сообщение готово к публикации в канал ", user_language) + f"«<b>{name_group.title}</b>»."
                public_mess1 = await translate_text("Вы хотите опубликовать публикацию прямо сейчас или отложить?", user_language)
                async with state.proxy() as data:
                    if any(key in data for key in ['photo', 'video', 'text', 'gif', 'document']):
                        await bot.send_message(user_id, public_mess, reply_markup=ReplyKeyboardRemove())
                        await bot.send_message(user_id, public_mess1, reply_markup=channelsend)
                    else:
                        await bot.send_message(user_id, await translate_text("Нет сообщений для публикации.", user_language))
            except ChatIdIsEmpty:
                await bot.send_message(user_id, text=await translate_text("Ошибка", user_language) , reply_markup=ReplyKeyboardRemove())
                await cmd_start_admin(message, state)


async def callback_create_post_select(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("group_id")
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    panelsend, panelsend_moder = await create_panelsend_markup(user_id)
    if group_id != None:
        await bot.answer_callback_query(call.id)
        if call.data == "back_post":
            send = await translate_text("Вы можете продолжить отправлять сообщения.", user_language)
            await bot.send_message(call.from_user.id, send, reply_markup=panelsend)
        elif call.data == "create_post_select":
            await sendStates.video.set()
            await sendStates.text.set()
            await sendStates.photo.set()
            await sendStates.gif.set()
            await sendStates.document.set()
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            text = await translate_text("Отправьте боту то, что хотите опубликовать. Это может быть всё, что угодно - текст, фото, видео, gif, файл", user_language)
            await bot.send_message(call.from_user.id, text, reply_markup=panelsend)


async def send_file(message: Message, state: FSMContext):
    user_id = message.from_user.id
    sendfile = await create_sendfile_markup(user_id)
    async with state.proxy() as data:
        content_type = message.content_type
        if content_type == ContentType.PHOTO:
            data['photo'] = message.photo[0].file_id
            data['text'] = message.caption
            await bot.send_photo(chat_id=message.chat.id, photo=data['photo'], caption=data['text'], reply_markup=sendfile)
            await state.finish()

        elif content_type == ContentType.VIDEO:
            data['video'] = message.video.file_id
            data['text'] = message.caption
            await bot.send_video(chat_id=message.chat.id, video=data['video'], caption=data['text'], reply_markup=sendfile)
            await state.finish()

        elif content_type == ContentType.ANIMATION:
            data['gif'] = message.animation.file_id
            data['text'] = message.caption
            await bot.send_animation(chat_id=message.chat.id, animation=data['gif'], caption=data['text'], reply_markup=sendfile)
            await state.finish()

        elif content_type == ContentType.DOCUMENT:
            data['document'] = message.document.file_id
            data['text'] = message.caption
            await bot.send_document(chat_id=message.chat.id, document=data['document'], caption=data['text'], reply_markup=sendfile)
            await state.finish()

        elif content_type == ContentType.TEXT:
            data['text'] = message.text
            await bot.send_message(chat_id=message.chat.id, text=data['text'], reply_markup=sendfile)
            await state.finish()


async def add_URL(call: CallbackQuery):
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    cancel_url = await create_keyboard_cancel_url(user_id)
    text = await translate_text("Пожалуйста, следуйте этому формату:\n\n<code>Кнопка 1 - http://example1.com\nКнопка 2 - http://example1.com</code>\n\nНажмите кнопку «Отмена», чтобы вернуться к добавлению сообщений.", user_language)
    await bot.send_message(call.from_user.id, text, reply_markup=cancel_url)
    await sendStates.url_buttons.set()


async def get_url_buttons(message: Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = None
    keyboard = InlineKeyboardMarkup(row_width=1)
    url_text = message.text
    buttons = url_text.split('\n')
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    if not re.match("^.* - https?://.*$", url_text, re.MULTILINE):
        text11 = await translate_text("Пожалуйста, следуйте этому формату:\n\n<code>Кнопка 1 - http://example1.com\nКнопка 2 - http://example1.com</code>\n\nНажмите кнопку «Отмена», чтобы вернуться к добавлению сообщений.", user_language)
        await message.reply(text11)
        return

    for button in buttons:
        button_data = button.split(' - ')
        if len(button_data) == 2 and re.match("^https?://.*$", button_data[1]):
            url_button = InlineKeyboardButton(text=button_data[0], url=button_data[1])
            button_added = False
            for row in keyboard.inline_keyboard:
                if url_button in row:
                    button_added = True
                    break
            if not button_added:
                keyboard.add(url_button)
        else:
            text12 = await translate_text("Пожалуйста, следуйте этому формату:\n\n<code>Кнопка 1 - http://example1.com\nКнопка 2 - http://example1.com</code>\n\nНажмите кнопку «Отмена», чтобы вернуться к добавлению сообщений.", user_language)
            await message.reply(text12)

    async with state.proxy() as data:
        data['url_buttons'] = keyboard
    await notsend_3_4(message, state, keyboard)


async def notsend_3_4(message: Message, state: FSMContext, keyboard: InlineKeyboardMarkup):
    user_id = message.from_user.id
    panelsend, panelsend_moder = await create_panelsend_markup(user_id)
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    send3 = InlineKeyboardButton(text = await translate_text("Удалить URL-кнопки", user_language), callback_data='delete_URL')
    send4 = InlineKeyboardButton(text = await translate_text("Удалить сообщение", user_language), callback_data='delete_message')
    async with state.proxy() as data:
        keyboard.add(send3, send4)
        if 'photo' in data:
            await bot.send_photo(chat_id=message.chat.id, photo=data['photo'], caption=data['text'], reply_markup=keyboard)
        elif 'video' in data:
            await bot.send_video(chat_id=message.chat.id, video=data['video'], caption=data['text'], reply_markup=keyboard)
        elif 'gif' in data:
            await bot.send_animation(chat_id=message.chat.id, animation=data['gif'], caption=data['text'], reply_markup=keyboard)
        elif 'document' in data:
            await bot.send_document(chat_id=message.chat.id, document=data['document'], caption=data['text'], reply_markup=keyboard)
        elif 'text' in data:
            await bot.send_message(chat_id=message.chat.id, text=data['text'], reply_markup=keyboard)
    text11 = await translate_text("URL-кнопки сохранены. Продолжайте отправлять сообщения.", user_language)
    await bot.send_message(chat_id=message.chat.id, text=text11, reply_markup=panelsend)


async def cancel_post(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        user_id = call.from_user.id
        message_id = data.get('message_id')
        chat_id = call.message.chat.id
        if message_id:
            await bot.delete_message(chat_id, message_id)
        await bot.delete_message(chat_id, call.message.message_id)
        data = await state.get_data()
        group_id = data.get("group_id")
        await state.finish()
        with sq.connect('my_db.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
            user_language_db = cursor.fetchone()
            user_language = user_language_db[0]
        text = await translate_text("Сообщения удалены.", user_language)
        await bot.send_message(call.message.chat.id, text)
        await StatesAdmin.ADMIN_GROUP_SELECTION.set()
        await state.update_data({'group_id': group_id})
        await sendStates.video.set()
        await sendStates.text.set()
        await sendStates.photo.set()
        await sendStates.gif.set()
        await sendStates.document.set()


async def delete_URL_buttons(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    sendfile = await create_sendfile_markup(user_id)
    data = await state.get_data()
    data.pop("url_buttons", None)
    await state.set_data(data)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    async with state.proxy() as data:
        if 'photo' in data:
            await bot.send_photo(chat_id=call.message.chat.id, photo=data['photo'], caption=data['text'], reply_markup=sendfile)
        elif 'video' in data:
            await bot.send_video(chat_id=call.message.chat.id, video=data['video'], caption=data['text'], reply_markup=sendfile)
        elif 'gif' in data:
            await bot.send_animation(chat_id=call.message.chat.id, animation=data['gif'], caption=data['text'], reply_markup=sendfile)
        elif 'document' in data:
            await bot.send_document(chat_id=call.message.chat.id, document=data['document'], caption=data['text'], reply_markup=sendfile)
        elif 'text' in data:
            await bot.send_message(chat_id=call.message.chat.id, text=data['text'], reply_markup=sendfile)


async def publish_post(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = call.from_user.id
    sendPostnext = await create_sendpostnext_markup(user_id)
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    group_id = data.get("group_id")
    name_group = await bot.get_chat(group_id)
    text1 = await translate_text("Вы уверены, что хотите опубликовать сообщение в канал", user_language) + f" «<b>{name_group.title}</b>»."
    await bot.send_message(chat_id=call.message.chat.id, text=text1, reply_markup=sendPostnext)
    await call.message.delete()



async def back_post_create(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    panelsend, panelsend_moder = await create_panelsend_markup(user_id)
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    try:
        text = await translate_text("Публикация отменена.", user_language)
        text1 = await translate_text("Вы можете продолжить отправлять сообщения.", user_language)
        await bot.send_message(chat_id=call.message.chat.id, text=text, reply_markup=panelsend)
        await bot.send_message(chat_id=call.message.chat.id, text=text1)
        await call.message.delete()
    except ChatIdIsEmpty:
        await cmd_start_admin(call.message, state)


async def back_post_create_next(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    channelsend = await create_channelsend_markup(user_id)
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    try:
        text = await translate_text("Вы хотите опубликовать пост прямо сейчас или отложить?", user_language)
        await bot.send_message(chat_id=call.message.chat.id, text=text, reply_markup=channelsend)
        await call.message.delete()
    except ChatIdIsEmpty:
        await cmd_start_admin(call.message, state)


async def send_post_channel(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with state.proxy() as data:
        data = await state.get_data()
        with sq.connect('my_db.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
            user_language_db = cursor.fetchone()
            user_language = user_language_db[0]
        group_id = data.get("group_id")
        chat_id=call.message.chat.id
        disable_web_page_preview, disable_notification = await get_user_settings(call.from_user.id)
        if 'url_buttons' in data:
            await bot.delete_message(chat_id, call.message.message_id)
            if 'photo' in data:
                await bot.send_photo(chat_id=group_id, photo=data['photo'], caption=data['text'], reply_markup=data['url_buttons'], disable_notification=disable_notification)
            elif 'video' in data:
                await bot.send_video(chat_id=group_id, video=data['video'], caption=data['text'], reply_markup=data['url_buttons'], disable_notification=disable_notification)
            elif 'gif' in data:
                await bot.send_animation(chat_id=group_id, animation=data['gif'], caption=data['text'], reply_markup=data['url_buttons'], disable_notification=disable_notification)
            elif 'document' in data:
                await bot.send_document(chat_id=group_id, document=data['document'], caption=data['text'], reply_markup=data['url_buttons'], disable_notification=disable_notification)
            elif 'text' in data:
                await bot.send_message(chat_id=group_id, text=data['text'], reply_markup=data['url_buttons'], disable_web_page_preview=disable_web_page_preview, disable_notification=disable_notification)
        else:
            await bot.delete_message(chat_id, call.message.message_id)
            if 'photo' in data:
                await bot.send_photo(chat_id=group_id, photo=data['photo'], caption=data['text'], disable_notification=disable_notification)
            elif 'video' in data:
                await bot.send_video(chat_id=group_id, video=data['video'], caption=data['text'], disable_notification=disable_notification)
            elif 'gif' in data:
                await bot.send_animation(chat_id=group_id, animation=data['gif'], caption=data['text'], disable_notification=disable_notification)
            elif 'document' in data:
                await bot.send_document(chat_id=group_id, document=data['document'], caption=data['text'], disable_notification=disable_notification)
            elif 'text' in data:
                await bot.send_message(chat_id=group_id, text=data['text'], disable_web_page_preview=disable_web_page_preview, disable_notification=disable_notification)

    name_group = await bot.get_chat(group_id)
    text_del = await translate_text("Сообщения успешно опубликованы на канале «<b>", user_language)+ f"{name_group.title}</b>»"
    await bot.send_message(chat_id=call.message.chat.id, text=text_del)
    await state.finish()
    await state.update_data(group_id=group_id)
    translated_text_1 = await translate_text("<b>Добро пожаловать в Админ-Панель!</b> \nЗдесь вы можете создавать посты, просматривать статистику канала «<b>", user_language)
    text_admin = translated_text_1 + f"{name_group.title}</b>»"
    admmarkup = await create_admin_markup(user_id)
    await bot.send_message(chat_id=call.message.chat.id, text=text_admin, reply_markup=admmarkup)


async def callback_menu(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    group_id = data.get("group_id")
    data = await state.get_data()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    name_group = (await bot.get_chat(group_id)).title
    admmarkup = await create_admin_markup(user_id)
    translated_text_1 = await translate_text("<b>Добро пожаловать в Админ-Панель!</b> \nЗдесь вы можете создавать посты, просматривать статистику канала «<b>", user_language)
    text_admin = translated_text_1 + name_group + "</b>»."
    await bot.send_message(call.message.chat.id, text_admin, reply_markup=admmarkup)

async def callback_menu_reduct(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    group_id = data.get("group_id")
    name_group = (await bot.get_chat(group_id)).title
    admmarkup = await create_admin_markup(user_id)
    translated_text_1 = await translate_text("<b>Добро пожаловать в Админ-Панель!</b> \nЗдесь вы можете создавать посты, просматривать статистику канала «<b>", user_language)
    text_admin = translated_text_1 + name_group + "</b>»."
    await call.message.edit_text(text_admin, reply_markup=admmarkup)


#-------------------------------|inline - Отложить публикацию|----------------------------------
def inline_markup_to_list(inline_markup):
    buttons_list = []
    for row in inline_markup.inline_keyboard:
        for button in row:
            buttons_list.append((button.text, button.url))
    return buttons_list


async def process_later_post(call: types.CallbackQuery):
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    message_text = await translate_text('Отправьте <b>время</b>, чтобы опубликовать сегодня.\nОтправьте <b>время</b> и <b>дату</b>, чтобы запланировать на любой другой день.'"Введите новое время для публикации.\n\nФорматы:\n"
                              "<code>дд.мм.гггг чч:мм</code>\n"
                              "<code>дд.мм чч:мм</code>\n"
                              "<code>чч:мм</code>", user_language)
    laterkey = await create_keyboard_laterkey(user_id)
    await bot.send_message(call.message.chat.id, message_text, reply_markup=laterkey)
    await call.message.delete()
    await sendStatesTime.waiting_time_today.set()


async def process_time_today(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        conn = await aiosqlite.connect('my_db.db')
        cursor = await conn.cursor()
        await cursor.execute("PRAGMA foreign_keys = ON")
        time_str = message.text.strip()
        data = await state.get_data()
        group_id = data.get("group_id")
        now = datetime.now(time_set)
        await cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = await cursor.fetchone()
        user_language = user_language_db[0]
        try:
            dt_naive = datetime.strptime(time_str, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                dt_naive = datetime.strptime(time_str, "%d.%m %H:%M")
                dt_naive = datetime.combine(datetime(now.year, dt_naive.month, dt_naive.day), dt_naive.time())
            except ValueError:
                time = datetime.strptime(time_str, "%H:%M").time()
                dt_naive = datetime.combine(now.date(), time)

        if dt_naive.date() > now.date() + timedelta(days=30):
            dat_err = await translate_text(f"Дата <code>{time_str}</code> должна быть в пределах одного месяца от текущей даты.", user_language)
            raise ValueError(dat_err)

        dt_aware = time_set.localize(dt_naive)
        month_name = calendar.month_name[dt_aware.month]
        name_group = await bot.get_chat(group_id)
        chat = message.chat.id
        mess = await translate_text("Публикация будет опубликована в", user_language)
        message_text = f"{mess} <b>«{name_group.title}»</b> - {dt_aware.strftime('%H:%M')}, {dt_aware.day} {month_name}."

        if dt_aware > now:
            await message.answer(message_text)
            await cmd_start_admin(message, state)

            async with state.proxy() as data:
                publish_time = dt_aware
                text = data.get('text', '')
                file = data.get('photo') or data.get('video') or data.get('gif') or data.get('document') or None
                file_type = None
                if file is not None:
                    if 'photo' in data:
                        file_type = 'photo'
                    elif 'video' in data:
                        file_type = 'video'
                    elif 'gif' in data:
                        file_type = 'gif'
                    elif 'document' in data:
                        file_type = 'document'
                else:
                    file_type = 'text'

                url_buttons = data.get('url_buttons')
                query = "INSERT INTO my_post (publish_time, file, file_type, text, id_group) VALUES (?, ?, ?, ?, ?)"
                values = (publish_time.strftime("%Y-%m-%d %H:%M:%S"), file, file_type, text, str(group_id))
                await cursor.execute(query, values)

                id_post = cursor.lastrowid
                if url_buttons and hasattr(url_buttons, 'inline_keyboard'):
                    url_buttons_list = inline_markup_to_list(url_buttons)
                    for button_text, button_url in url_buttons_list:
                        query = "INSERT INTO buttons (text, url, id_post) VALUES (?, ?, ?)"
                        values = (button_text, button_url, id_post)
                        await cursor.execute(query, values)

                await conn.commit()

                time_to_sleep = (publish_time - datetime.now(time_set)).total_seconds()
                if time_to_sleep > 0:
                    await asyncio.sleep(time_to_sleep)
                try:
                    user_id = message.from_user.id
                    disable_web_page_preview, disable_notification = await get_user_settings(user_id)
                    sent_message = None
                    if file_type == 'photo':
                        sent_message = await bot.send_photo(chat_id=group_id, photo=file, caption=text, reply_markup=url_buttons if url_buttons else None,
                                                            disable_notification=disable_notification)
                    elif file_type == 'video':
                        sent_message = await bot.send_video(chat_id=group_id, video=file, caption=text, reply_markup=url_buttons if url_buttons else None,
                                                            disable_notification=disable_notification)
                    elif file_type == 'gif':
                        sent_message = await bot.send_animation(chat_id=group_id, animation=file, caption=text, reply_markup=url_buttons if url_buttons else None,
                                                                disable_notification=disable_notification)
                    elif file_type == 'document':
                        sent_message = await bot.send_document(chat_id=group_id, document=file, caption=text, reply_markup=url_buttons if url_buttons else None,
                                                            disable_notification=disable_notification)
                    elif file_type == 'text':
                        sent_message = await bot.send_message(chat_id=group_id, text=text, reply_markup=url_buttons if url_buttons else None,
                                                            disable_web_page_preview=disable_web_page_preview, disable_notification=disable_notification)
                    if sent_message:
                        message_id = sent_message.message_id
                        await cursor.execute("UPDATE my_post SET message_id = ? WHERE id_post = ?", (message_id, id_post))
                        await conn.commit()

                except Exception as e:
                    print(f"Failed to publish post {chat}: {e}")
                else:
                    await message.delete()
        else:
            ans = await translate_text(f"Указанное время <code>{time_str}</code> уже прошло.", user_language)
            await message.answer(ans)
    except ValueError as e:
        messans = await translate_text("Некорректный формат времени, попробуйте еще раз:", user_language)
        laterkey = await create_keyboard_laterkey(user_id)
        await message.answer(f"{messans} {e}", reply_markup=laterkey)
    except Exception as e:
        print(e)
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()



#-------------------------------|Редактировать главное меню|----------------------------------


async def callback_editing_post(call: types.CallbackQuery):
    await call.message.edit_text("Перешлите сообщение из канала, которое вы хотите отредактировать.", reply_markup = home_menu1)
    await reductPost.reductstarted.set()


async def forwarded_message_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['channel_id'] = message.forward_from_chat.id
        data['message_id'] = message.forward_from_message_id
    data = await state.get_data()
    group_id = data.get("group_id")
    content_type = message.content_type
    name_group = (await bot.get_chat(group_id)).title
    if message.forward_from_chat:
        if str(message.forward_from_chat.id) == str(group_id):
            async with state.proxy() as data:
                mark1 = None
                if message.reply_markup:

                    data['url_buttons'] = message.reply_markup
                    if 'url_buttons' in data:
                        mark1 = data.get('url_buttons')

                if content_type == ContentType.PHOTO:
                    data['photo'] = message.photo[0].file_id
                    data['text'] = message.caption
                    if 'url_buttons' in data:
                        mark = types.InlineKeyboardMarkup()
                        for row in mark1.inline_keyboard:
                            mark.row(*row)
                        mark.add(r1).add(r2).add(r3).add(r4)
                        await bot.send_photo(chat_id=message.from_user.id, photo=data['photo'], caption=data['text'], reply_markup=mark)
                    else:
                        await bot.send_photo(chat_id=message.from_user.id, photo=data['photo'], caption=data['text'], reply_markup=reduct_message)

                elif content_type == ContentType.VIDEO:
                    data['video'] = message.video.file_id
                    data['text'] = message.caption
                    if 'url_buttons' in data:
                        mark = types.InlineKeyboardMarkup()
                        for row in mark1.inline_keyboard:
                            mark.row(*row)
                        mark.add(r1).add(r2).add(r3).add(r4)
                        await bot.send_video(chat_id=message.from_user.id, video=data['video'], caption=data['text'], reply_markup=mark)
                    else:
                        await bot.send_video(chat_id=message.from_user.id, video=data['video'], caption=data['text'], reply_markup=reduct_message)

                elif content_type == ContentType.ANIMATION:
                    data['gif'] = message.animation.file_id
                    data['text'] = message.caption
                    if 'url_buttons' in data:
                        mark = types.InlineKeyboardMarkup()
                        for row in mark1.inline_keyboard:
                            mark.row(*row)
                        mark.add(r1).add(r2).add(r3).add(r4)
                        await bot.send_animation(chat_id=message.from_user.id, animation=data['gif'], caption=data['text'], reply_markup=mark)
                    else:
                        await bot.send_animation(chat_id=message.from_user.id, animation=data['gif'], caption=data['text'], reply_markup=reduct_message)

                elif content_type == ContentType.DOCUMENT:
                    data['document'] = message.document.file_id
                    data['text'] = message.caption
                    if 'url_buttons' in data:
                        mark = types.InlineKeyboardMarkup()
                        for row in mark1.inline_keyboard:
                            mark.row(*row)
                        mark.add(r1).add(r2).add(r3).add(r4)
                        await bot.send_document(chat_id=message.from_user.id, document=data['document'], caption=data['text'], reply_markup=mark)
                    else:
                        await bot.send_document(chat_id=message.from_user.id, document=data['document'], caption=data['text'], reply_markup=reduct_message)


                elif content_type == ContentType.TEXT:
                    data['text'] = message.text
                    if 'url_buttons' in data:
                        mark = types.InlineKeyboardMarkup()
                        for row in mark1.inline_keyboard:
                            mark.row(*row)
                        mark.add(r1).add(r2).add(r3).add(r4)
                        await bot.send_message(chat_id=message.from_user.id, text=data['text'], reply_markup=url_buttons)
                    else:
                        await bot.send_message(chat_id=message.from_user.id, text=data['text'], reply_markup=reduct_message)
                else:
                    await bot.send_message(chat_id=message.from_user.id, text="Я не могу обработь ваше сообщение")
                url_buttons = None
                await reductPost.reduct.set()
        else:
            await bot.send_message(chat_id=message.from_user.id, text=f"Сообщение которое вы прислали не из <b>{name_group}</b>")
            return
    else:
        await bot.send_message(chat_id=message.from_user.id, text=f"Нужно переслать сообщение из группы <b>{name_group}</b> чтобы его можно было редактировать")
        return


async def reduct_next_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    async with state.proxy() as data:
        content_type = message.content_type

        if content_type == ContentType.PHOTO:
            data['photo'] = message.photo[0].file_id
            data['text'] = message.caption
        elif content_type == ContentType.VIDEO:
            data['video'] = message.video.file_id
            data['text'] = message.caption
        elif content_type == ContentType.ANIMATION:
            data['gif'] = message.animation.file_id
            data['text'] = message.caption
        elif content_type == ContentType.DOCUMENT:
            data['document'] = message.document.file_id
            data['text'] = message.caption
        elif content_type == ContentType.TEXT:
            data['text'] = message.text
        else:
            await message.answer("Пожалуйста, отправьте сообщение с текстом.")
            return



    if 'url_buttons' in data:
        mark1 = data.get('url_buttons')
        mark = types.InlineKeyboardMarkup()
        for row in mark1.inline_keyboard:
            mark.row(*row)
        mark.add(r1).add(r2).add(r3).add(r4)

        if 'photo' in data:
            await bot.send_photo(chat_id=user_id, photo=data['photo'], caption=data.get('text', ''), reply_markup=mark)
        elif 'video' in data:
            await bot.send_video(chat_id=user_id, video=data['video'], caption=data.get('text', ''), reply_markup=mark)
        elif 'gif' in data:
            await bot.send_animation(chat_id=user_id, animation=data['gif'], caption=data.get('text', ''), reply_markup=mark)
        elif 'document' in data:
            await bot.send_document(chat_id=user_id, document=data['document'], caption=data.get('text', ''), reply_markup=mark)
        elif 'text' in data:
            await bot.send_message(chat_id=user_id, text=data['text'], reply_markup=mark)
    else:
        if 'photo' in data:
            await bot.send_photo(chat_id=user_id, photo=data['photo'], caption=data.get('text', ''), reply_markup=reduct_message)
        elif 'video' in data:
            await bot.send_video(chat_id=user_id, video=data['video'], caption=data.get('text', ''), reply_markup=reduct_message)
        elif 'gif' in data:
            await bot.send_animation(chat_id=user_id, animation=data['gif'], caption=data.get('text', ''), reply_markup=reduct_message)
        elif 'document' in data:
            await bot.send_document(chat_id=user_id, document=data['document'], caption=data.get('text', ''), reply_markup=reduct_message)
        elif 'text' in data:
            await bot.send_message(chat_id=user_id, text=data['text'], reply_markup=reduct_message)



async def callback_save_reduct(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    text = data.get("text")
    url_buttons = data.get('url_buttons')
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]

    keyboard = url_buttons
    try:
        if 'text' in data:
            try:
                await bot.edit_message_text(chat_id=data['channel_id'], message_id=data['message_id'], text=text, reply_markup=keyboard)
            except:
                try:
                    await bot.edit_message_caption(chat_id=data['channel_id'], message_id=data['message_id'], caption=text, reply_markup=keyboard)
                except:
                    return await call.message.answer('Ошибка')
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            group_id = data.get("channel_id")
            await state.finish()
            await state.update_data({'group_id': group_id})
            await bot.send_message(chat_id=call.from_user.id, text="Сообщение было отредактировано")
            name_group = (await bot.get_chat(group_id)).title
            admmarkup = await create_admin_markup(user_id)
            translated_text_1 = await translate_text("<b>Добро пожаловать в Админ-Панель!</b> \nЗдесь вы можете создавать посты, просматривать статистику канала «<b>", user_language)
            text_admin = translated_text_1 + name_group + "</b>»."
            await bot.send_message(user_id, text_admin, reply_markup=admmarkup)

    except (BotBlocked, ChatNotFound, MessageNotModified, MessageToDeleteNotFound, MessageCantBeEdited) as e:
        print(e)
        await bot.send_message(chat_id=call.from_user.id, text="Боту не разрешено редактировать сообщения в этой группе. Пожалуйста, проверьте настройки разрешений.")


#-------------------------------|Отложенные главное меню|----------------------------------


async def callback_deferred_post(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    data = await state.get_data()
    group_id = data.get("group_id")

    data['photo'] = ""
    data['video'] = ""
    data['gif'] = ""
    data['document'] = ""
    data['text'] = ""
    try:
        await cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = await cursor.fetchone()
        user_language = user_language_db[0]

        await cursor.execute("SELECT publish_time, file, file_type, text, url_buttons, id_group FROM my_post WHERE id_group=? AND message_id IS NULL", (group_id,))
        results = await cursor.fetchall()
        buttons = []
        found_posts = False
        for row in results:
            found_posts = True
            publish_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            button_name = publish_time.strftime("%d.%m.%Y %H:%M")
            data['publish_time'] = button_name
            await state.update_data(publish_time=button_name)
            buttons.append(InlineKeyboardButton(text=button_name, callback_data=f"show_post_{button_name}"))
        if found_posts:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+1] for i in range(0, len(buttons), 1)])
            reply_markup.add(home1)
            await call.message.delete()
            ot = await translate_text("Выберите отложенный пост, который вы хотите посмотреть или удалить.", user_language)
            await bot.send_message(call.message.chat.id, ot, reply_markup=reply_markup)
        else:
            await call.message.delete()
            no = await translate_text("Публикаций нету", user_language)
            await bot.send_message(call.message.chat.id, no, reply_markup=home_menu1)
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()

# удалить
async def confirm_delete_callback_query_handler(call: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    data = await state.get_data()
    post_time_str = data.get("publish_time")
    buttons = InlineKeyboardMarkup()
    b2 = InlineKeyboardButton(text="Удалить", callback_data=f"delete_post_{post_time_str}")
    b1 = InlineKeyboardButton(text="« Назад", callback_data="cancel_delete")
    buttons.add(b1, b2)
    await bot.send_message(call.message.chat.id, "Публикация будет удалена. Продолжить?", reply_markup=buttons)


async def delete_post_callback_query_handler(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    post_time_str = data.get("publish_time")
    group_id = data.get("group_id")

    post_time = datetime.strptime(post_time_str, "%d.%m.%Y %H:%M")
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    try:
        await cursor.execute("DELETE FROM my_post WHERE id_group=? AND publish_time=?", (group_id, post_time))
        await conn.commit()
        await bot.send_message(call.message.chat.id, "Публикация успешно удалена.")
        await callback_deferred_post(call, state)
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()


# изменить время
async def show_post_callback_query_handler(call: types.CallbackQuery, state: FSMContext):
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    try:
        data = await state.get_data()
        publish_time_str = data.get("publish_time")
        publish_time = datetime.strptime(publish_time_str, "%d.%m.%Y %H:%M")
        await cursor.execute("SELECT id_post, file, file_type, text FROM my_post WHERE publish_time=?", (publish_time.strftime("%Y-%m-%d %H:%M:%S"),))
        result = await cursor.fetchone()
        if result is None:
            await bot.send_message(call.message.chat.id, "За это время сообщений не найдено.")
            return
        id_post, file, file_type, text = result

        await cursor.execute("SELECT text, url FROM buttons WHERE id_post=?", (id_post,))
        button_results = await cursor.fetchall()
        data['post_id'] = id_post
        await state.update_data(post_id=id_post)
        url_buttons = None
        url_buttons = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=row[0], url=row[1])] for row in button_results])
        url_buttons.add(InlineKeyboardButton(text="Изменить время", callback_data=f"change_time_{id_post}")).add(d2).add(d3)
        await call.message.delete()
        if file:
            if file_type == 'photo':
                await bot.send_photo(call.message.chat.id, photo=file, caption=text, reply_markup=url_buttons)
            elif file_type == 'video':
                await bot.send_video(call.message.chat.id, video=file, caption=text, reply_markup=url_buttons)
            elif file_type == 'gif':
                await bot.send_animation(call.message.chat.id, animation=file, caption=text, reply_markup=url_buttons)
            elif file_type == 'document':
                await bot.send_document(call.message.chat.id, document=file, caption=text, reply_markup=url_buttons)
        else:
            await bot.send_message(call.message.chat.id, text=text, reply_markup=url_buttons)
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()


async def callback_cancel_delete(call: types.CallbackQuery, state: FSMContext):
    await show_post_callback_query_handler(call, state)


async def callback_back_list_public(call: types.CallbackQuery, state: FSMContext):
    await callback_deferred_post(call, state)


async def callback_change_time_public(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    b1 = InlineKeyboardButton(text="« Назад", callback_data="cancel_delete")
    buttons = InlineKeyboardMarkup().add(b1)
    await call.message.answer("Введите новое время для публикации. Форматы:\n"
                            "<code>дд.мм.гггг чч:мм</code>\n"
                            "<code>дд.мм чч:мм</code>\n"
                            "<code>чч:мм</code>", reply_markup=buttons)
    await ChangeTimeStates.new_time.set()


async def change_post_time(message: types.Message, state: FSMContext):
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    new_time_str = message.text.strip()
    try:
        now = datetime.now()
        try:
            new_dt = datetime.strptime(new_time_str, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                new_dt = datetime.strptime(new_time_str, "%d.%m %H:%M")
                new_dt = new_dt.replace(year=now.year)
            except ValueError:
                time = datetime.strptime(new_time_str, "%H:%M").time()
                new_dt = datetime.combine(now.date(), time)
        if new_dt < now:
            raise ValueError("Введенное время уже прошло")
        async with state.proxy() as data:
            post_id = data["post_id"]
        await cursor.execute("UPDATE my_post SET publish_time=? WHERE id_post=?", (new_dt.strftime("%Y-%m-%d %H:%M:%S"), post_id))
        await conn.commit()
        await message.answer(f"Время публикации успешно изменено на {new_dt.strftime('%d.%m.%Y %H:%M')}")

    except ValueError as e:
        await message.answer(f"Некорректный формат времени, попробуйте еще раз: {e}")
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(cmd_start_admin, commands = ['admin'], state='*')
    dp.register_callback_query_handler(main_menu_list, text='groups_start', state='*')
    dp.register_callback_query_handler(callback_menu, text='home_menu', state='*')
    dp.register_callback_query_handler(callback_menu_reduct, text='home_menu_reduct', state='*')

    dp.register_message_handler(cancel_post_now, text='Отменить', state='*')
    dp.register_message_handler(cancel_post_now, text='Cancel', state='*')
    dp.register_message_handler(cancel_post_now, text='Скасувати', state='*')

    dp.register_message_handler(cancel1_post, text='Отмена', state='*')
    dp.register_message_handler(cancel1_post, text='Cancell', state='*')
    dp.register_message_handler(cancel1_post, text='Відміна', state='*')

    dp.register_message_handler(clear_post, text='Очистить', state='*')
    dp.register_message_handler(clear_post, text='Clear', state='*')
    dp.register_message_handler(clear_post, text='Очистити', state='*')

    dp.register_message_handler(preview_post, text='Предпросмотр', state='*')
    dp.register_message_handler(preview_post, text='Preview', state='*')
    dp.register_message_handler(preview_post, text='Попередній перегляд', state='*')

    dp.register_message_handler(next_post, text='Далее', state='*')
    dp.register_message_handler(next_post, text='Next', state='*')
    dp.register_message_handler(next_post, text='Далі', state='*')

    dp.register_callback_query_handler(callback_create_post_select, text='create_post_select', state='*')
    dp.register_message_handler(send_file, content_types=[ContentType.PHOTO, ContentType.VIDEO, ContentType.TEXT, ContentType.ANIMATION, ContentType.DOCUMENT], state=[sendStates.photo, sendStates.video, sendStates.text, sendStates.gif, sendStates.document])
    dp.register_callback_query_handler(add_URL, text='add_URL', state='*')
    dp.register_message_handler(get_url_buttons, content_types=['any'], state=sendStates.url_buttons)
    dp.register_callback_query_handler(cancel_post, text='delete_message', state='*')
    dp.register_callback_query_handler(publish_post, text='send_post', state='*')
    dp.register_callback_query_handler(back_post_create, text='back_Post', state='*')
    dp.register_callback_query_handler(back_post_create_next, text='back_next_post', state='*')
    dp.register_callback_query_handler(send_post_channel, text='next_send_post', state='*')
    dp.register_callback_query_handler(process_later_post, text='later_post', state='*')
    dp.register_message_handler(process_time_today, state=sendStatesTime.waiting_time_today)
    dp.register_callback_query_handler(process_group_selection, lambda c: c.data and c.data.startswith('group_'), state='*')
    dp.register_callback_query_handler(callback_editing_post, text='editing_post', state='*')
    dp.register_message_handler(forwarded_message_handler, content_types=[ContentType.PHOTO, ContentType.VIDEO, ContentType.TEXT, ContentType.ANIMATION, ContentType.DOCUMENT], state=reductPost.reductstarted)
    dp.register_message_handler(reduct_next_message, content_types=[ContentType.PHOTO, ContentType.VIDEO, ContentType.TEXT, ContentType.ANIMATION, ContentType.DOCUMENT], state=reductPost.reduct)
    dp.register_callback_query_handler(callback_save_reduct, text='save_reduct', state='*')
    dp.register_callback_query_handler(delete_URL_buttons, text='delete_URL', state='*')

    dp.register_callback_query_handler(callback_change_time_public, lambda call: call.data.startswith('change_time_'), state='*')
    dp.register_message_handler(change_post_time, state=ChangeTimeStates.new_time)
    dp.register_callback_query_handler(show_post_callback_query_handler, lambda call: call.data.startswith("show_post_"), state='*')

    dp.register_callback_query_handler(callback_cancel_delete, text='cancel_delete', state='*')
    dp.register_callback_query_handler(callback_back_list_public, text='back_list_public', state='*')


    #удалиние отложенного
    dp.register_callback_query_handler(confirm_delete_callback_query_handler, text='delete_public', state='*')
    dp.register_callback_query_handler(delete_post_callback_query_handler, text_startswith="delete_post_", state='*')
    dp.register_callback_query_handler(callback_deferred_post, text='deferred_post', state='*')
