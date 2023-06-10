from loader import *
from config import get_admins
import sqlite3 as sq
from data.db import *
from buttons.admin_kb import *
from handlers.admin_hand import StatesAdmin


class RegisterChannel(StatesGroup):
    channel_id = State()


conn = sq.connect('my_db.db')
cursor = conn.cursor()


async def cmd_super_admin(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    if message.from_user.id in get_admins():
        full_name = message.from_user.full_name
        user_id = message.from_user.id
        welcome_message = await translate_text(f"Добро пожаловать <b>{full_name}</b> | Ваш id: <code>{user_id}</code>\n\nЗдесь вы можете посмотреть список групп, в которых можно сделать публикацию, а так же добавить и удалить из списка.", user_language)
        list_back, super_menu, list_nullsup, list_null = await create_keyboard_super_admin(user_id)
        await bot.send_message(user_id, welcome_message, reply_markup=super_menu)
        await create_db()


async def callback_add_channel(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    bot_username = await bot.get_me()
    instuction = await translate_text(f"<b>Добавление канала</b>\n\nЧтобы добавить канал, вы должны выполнить два следующих шага:\n\n1. Добавьте @{bot_username.username} в администраторы вашего канала.\n2. Перешлите мне любое сообщение из вашего канала (вы также можете отправить <a href='https://telegra.ph/Kak-dobavit-chat-ili-supergruppu-04-24/'>Group ID</a>).", user_language)
    list_back, super_menu, list_nullsup, list_null = await create_keyboard_super_admin(user_id)
    await bot.send_message(call.message.chat.id, instuction, disable_web_page_preview=True, reply_markup=list_back)
    await RegisterChannel.channel_id.set()



async def handle_channel_id(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    user_id = message.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    try:
        if message.text and message.text.startswith('-') and message.text[1:].isdigit():
            group_id = str(message.text)
        elif message.forward_from_chat:
            group_id = str(message.forward_from_chat.id)
        else:
            await bot.send_message(message.chat.id, await translate_text("Не удалось получить информацию о чате. Попробуйте еще раз.", user_language))
            return

        chatbot = await bot.get_chat(group_id)
        chat_member = await bot.get_chat_member(group_id, bot.id)

        if chat_member.status in (types.ChatMemberStatus.CREATOR, types.ChatMemberStatus.ADMINISTRATOR):
            name_group = chatbot.username or f"{chatbot}"
            name_group = name_group.replace(" ", "")

            admin_ids = get_admins()
            cursor.execute("SELECT id_group FROM my_group WHERE id_group=?", (group_id,))
            result = cursor.fetchone()

            if result:
                await bot.send_message(message.chat.id, await translate_text(f"Группа @{name_group} с ID <code>{group_id}</code> уже есть в базе данных.", user_language))
                existing_admin_ids = result[1].split(', ')
                for admin_id in admin_ids:
                    if str(admin_id) not in existing_admin_ids:
                        new_id_admin = result[1] + str(admin_id) + ', '
                        cursor.execute("UPDATE my_group SET id_admin = ? WHERE id_group = ?", (new_id_admin, group_id))
                        conn.commit()
            else:
                cursor.execute("INSERT INTO my_group (id_group, id_admin) VALUES (?, ?)", (str(group_id), ', '.join(map(str, admin_ids)) + ', '))
                conn.commit()
                await bot.send_message(message.chat.id, await translate_text(f"Группа успешно добавлена ID: <code>{group_id}</code>", user_language))
                await state.finish()
                await state.update_data({'lang': user_language})
                await cmd_super_admin(message, state)
        else:
            await bot.send_message(message.chat.id, await translate_text(f"Бот не является администратором в этой группы", user_language))
            return
    except ChatNotFound:
        cht = await translate_text("Чат не найден", user_language)
        await bot.send_message(message.chat.id, f"{cht}: <code>{group_id}</code>")
        return
    except Exception as e:
        print(e)
        return
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


async def callback_back_menu(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    welcome_message = await translate_text(f"Ваш id: <code>{user_id}</code>\n\nЗдесь вы можете посмотреть список групп, в которых можно сделать публикацию, а так же добавить и удалить из списка.", user_language)
    list_back, super_menu, list_nullsup, list_null = await create_keyboard_super_admin(user_id)
    await call.message.edit_text(welcome_message, disable_web_page_preview=True, reply_markup=super_menu)


async def callback_list_channel(call: types.CallbackQuery, state: FSMContext):
    list_groups_all = InlineKeyboardMarkup()
    user_id = call.from_user.id
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    try:
        cursor.execute("SELECT id_group FROM my_group")
        id_groups = [row[0] for row in cursor.fetchall()]

        message_text = await translate_text('Выберите канал, в который вы хотите создать пост.', user_language)
        if len(id_groups) == 0:
            message_text = await translate_text('Список групп пуст.', user_language)
            list_nullsup = await create_keyboard_super_admin(user_id)
            await call.message.edit_text(message_text, reply_markup=list_nullsup)
            return

        groups_to_remove = []
        for group_id in id_groups:
            try:
                chat_member = await bot.get_chat_member(group_id, bot.id)
                if not chat_member.status == 'administrator':
                    groups_to_remove.append(group_id)
            except:
                groups_to_remove.append(group_id)
        for group_id in groups_to_remove:
            id_groups.remove(group_id)
            cursor.execute("DELETE FROM my_group WHERE id_group = ?", (group_id,))
            conn.commit()

        num_buttons_per_row = 2
        for i in range(0, len(id_groups), num_buttons_per_row):
            row = []
            for j in range(i, min(i+num_buttons_per_row, len(id_groups))):
                group_id = id_groups[j]
                group_chat = await bot.get_chat(group_id)
                button_text = group_chat.title
                button_callback_data = f'group_{j+1}'
                row.append(InlineKeyboardButton(text=button_text, callback_data=button_callback_data))
            list_groups_all.row(*row)
        await state.set_state(StatesAdmin.ADMIN_GROUP_SELECTION)
        but = "« " + await translate_text('Назад', user_language)
        back_menu_button = InlineKeyboardButton(text=but, callback_data='back_menu')
        list_groups_all.add(back_menu_button)
        await call.message.edit_text(message_text, reply_markup=list_groups_all)
        await state.update_data(group_id=group_id)
    except sq.ProgrammingError as err:
        if str(err) == 'Cannot operate on a closed cursor.':
            cursor = conn.cursor()
            return await callback_list_channel(call)
        raise err


async def delete_list_channel(call: types.CallbackQuery, state: FSMContext):
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    try:
        cursor.execute("SELECT id_group FROM my_group")
        id_groups = [row[0] for row in cursor.fetchall()]

        if len(id_groups) == 0:
            message_text = await translate_text('Список групп пуст.', user_language)
            await call.message.edit_text(message_text)
            return

        message_text = await translate_text('Выберите группу для удаления:', user_language)
        list_groups_all = InlineKeyboardMarkup()
        num_buttons_per_row = 2

        for i in range(0, len(id_groups), num_buttons_per_row):
            row = []
            for j in range(i, min(i+num_buttons_per_row, len(id_groups))):
                group_id = id_groups[j]
                group_chat = await bot.get_chat(group_id)
                button_text = group_chat.title
                button_callback_data = f'remove_group_{group_id}'
                row.append(InlineKeyboardButton(text=button_text, callback_data=button_callback_data))
            list_groups_all.row(*row)
        b = "« " + await translate_text("Назад", user_language)
        back_menu_button = InlineKeyboardButton(text=b, callback_data='back_menu')
        list_groups_all.add(back_menu_button)
        await call.message.edit_text(message_text, reply_markup=list_groups_all)

    except sq.ProgrammingError as err:
        if str(err) == 'Cannot operate on a closed cursor.':
            cursor = conn.cursor()
            return await delete_list_channel(call)
        raise err


async def callback_remove_group(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    group_id = call.data.split('_')[-1]
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    message_text = await translate_text('Вы уверены, что хотите удалить группу?', user_language)
    confirm_buttons = InlineKeyboardMarkup(row_width=2)
    but = "« " + await translate_text('Назад', user_language)
    delete_button = InlineKeyboardButton(text=await translate_text('Удалить', user_language), callback_data=f'confirm_delete_group_{group_id}')
    cancel_button = InlineKeyboardButton(text=but,callback_data='delete_channel')
    confirm_buttons.add(delete_button, cancel_button)
    await call.message.edit_text(message_text, reply_markup=confirm_buttons)


async def callback_confirm_delete_group(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    group_id = call.data.split('_')[-1]
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM my_group WHERE id_group = ?", (group_id,))
        conn.commit()
        text = await translate_text('Группа успешно удалена.', user_language)
        await bot.answer_callback_query(callback_query_id=call.id, text=text)
    except sq.ProgrammingError as err:
        if str(err) == 'Cannot operate on a closed cursor.':
            cursor = conn.cursor()
            return await callback_confirm_delete_group(call)
        raise err
    finally:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await callback_back_menu(call.message, state)


async def callback_cancel_delete_group(call: types.CallbackQuery, state: FSMContext):
    await callback_back_menu(call.message, state)



def register_handlers_super_admin(dp: Dispatcher):
    dp.register_message_handler(cmd_super_admin, commands = ['superadmin'], state='*')
    dp.register_callback_query_handler(callback_add_channel, text='add_channel', state='*')
    dp.register_callback_query_handler(callback_list_channel, text='list_groups', state='*')
    dp.register_callback_query_handler(delete_list_channel, text_startswith='delete_channel', state='*')
    dp.register_callback_query_handler(callback_remove_group, text_startswith='remove_group_', state='*')
    dp.register_callback_query_handler(callback_confirm_delete_group, text_startswith='confirm_delete_group_', state='*')
    dp.register_callback_query_handler(callback_cancel_delete_group, text='cancel_delete_group', state='*')
    dp.register_message_handler(handle_channel_id, state=RegisterChannel.channel_id)
    dp.register_callback_query_handler(callback_back_menu, text='back_menu', state='*')
