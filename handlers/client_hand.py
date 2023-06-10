from loader import *
from handlers.other_hand import *
from data.db import *
from data.db import sq, setting_admin

conn = sq.connect('my_db.db')
cursor = conn.cursor()

async def cmd_start_client(message: types.Message, state: FSMContext):
    await state.finish()
    await create_db_post()
    await create_url_buttons()
    await setting_interaction()
    await create_banned_users_table()

    user_id = message.from_user.id
    full_name = message.from_user.full_name
    interaction_time = datetime.now()

    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        if user_language_db is None:
            user_language = message.from_user.language_code
            cursor.execute(
                "INSERT INTO users_interaction (user_id, full_name, first_interaction, last_interaction, language) VALUES (?, ?, ?, ?, ?)",
                (user_id, full_name, interaction_time, interaction_time, user_language)
            )
        else:
            user_language = user_language_db[0]
            cursor.execute(
                "UPDATE users_interaction SET last_interaction = ?, language = ? WHERE user_id = ?",
                (interaction_time, user_language, user_id)
            )
        conn.commit()

        cursor.execute("SELECT id_group, id_admin FROM my_group")
        id_groups_admins = cursor.fetchall()
        is_admin = False
        for group_id, id_admin in id_groups_admins:
            try:
                chat_member = await bot.get_chat_member(group_id, user_id)
                id_admin_list = id_admin.split(', ')
                if chat_member.status == 'administrator' or chat_member.status == 'creator' or user_id in get_admins():
                    is_admin = True
                    if str(user_id) not in id_admin_list:
                        new_id_admin = id_admin + str(user_id) + ', '
                        cursor.execute("UPDATE my_group SET id_admin = ? WHERE id_group = ?", (new_id_admin, group_id))
                        conn.commit()
                elif str(user_id) in id_admin_list:
                    id_admin_list.remove(str(user_id))
                    new_id_admin = ', '.join(id_admin_list)
                    cursor.execute("UPDATE my_group SET id_admin = ? WHERE id_group = ?", (new_id_admin, group_id))
                    conn.commit()
            except:
                pass

        if user_id in get_admins() or is_admin:
            if user_id in get_admins():
                text = await translate_text("Чтобы войти в админ панель нажми \n/admin\nЧтобы добавить группу нажми \n/superadmin", user_language)
                await bot.send_message(user_id, text, reply_markup=ReplyKeyboardRemove())
                await setting_admin()
            else:
                text = await translate_text("Чтобы войти в админ панель нажми \n/admin", user_language)
                await bot.send_message(user_id, text, reply_markup=ReplyKeyboardRemove())
                await setting_admin()
            await set_start_admin(dp, message.chat.id, user_id, user_language)
        else:
            text = await translate_text("Привет! Если у тебя есть вопросы к администрации нажми /support чтобы начать переписку", user_language)
            await set_default_command(dp, message.chat.id, user_language)
            await bot.send_message(user_id, text, reply_markup=ReplyKeyboardRemove())


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(cmd_start_client, commands=['start'], state='*')
