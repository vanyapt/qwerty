from loader import *
from config import *
from data.db import create_banned_users_table
from buttons.admin_kb import *

class ModerationState(StatesGroup):
    waiting_for_user_info = State()

async def mute(message: types.Message):
    await create_banned_users_table()
    bot_member = await bot.get_chat_member(message.chat.id, bot.id)
    if bot_member.status == 'member':
        await message.reply("Я не являюсь администратором этого чата!")
        return
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in (types.ChatMemberStatus.CREATOR, types.ChatMemberStatus.ADMINISTRATOR) in get_admins():
        await message.reply("Эта команда доступна только для администраторов!")
        return
    name1 = message.from_user.get_mention(as_html=True)
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на сообщение!")
        return
    try:
        muteint = int(message.text.split()[1])
        mutetype = message.text.split()[2]
        comment = " ".join(message.text.split()[3:])
    except IndexError:
        await message.reply('Не хватает аргументов!\nПример:\n`/мут 1 ч причина`')
        return

    if mutetype in ("ч", "часов", "час", "м", "минут", "минуты", "д", "дней", "день"):
        if mutetype in ("ч", "часов", "час"):
            if muteint <= 23:
                dt = datetime.now() + timedelta(hours=muteint)
            else:
                await message.reply('Можно дать мут не больше 23 часов!')
                return
        elif mutetype in ("м", "минут", "минуты"):
            if muteint <= 59:
                dt = datetime.now() + timedelta(minutes=muteint)
            else:
                await message.reply('Можно дать мут не больше 59 минут!')
                return
        elif mutetype in ("д", "дней", "день"):
            if muteint <= 7:
                dt = datetime.now() + timedelta(days=muteint)
            else:
                await message.reply('Можно дать мут не больше 7 дней!')
                return
        timestamp = dt.timestamp()
        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            types.ChatPermissions(False),
            until_date=timestamp
        )

        conn = await aiosqlite.connect('my_db.db')
        cursor = await conn.cursor()
        await cursor.execute(
            """
            INSERT OR REPLACE INTO banned_users
            (user_id, banned_by_id, ban_time, group_id, ban_reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message.reply_to_message.from_user.id, message.from_user.id, dt.strftime("%Y-%m-%d %H:%M:%S"), message.chat.id, comment))
        await conn.commit()
        await cursor.close()
        await conn.close()

        await message.reply(
        f'| <b>Решение было принято:</b> {name1}\n'
        f'| <b>Нарушитель:</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">'
        f'{message.reply_to_message.from_user.first_name}</a>\n'
        f'|<b> ID нарушителя:</b><code> {message.reply_to_message.from_user.id}</code>\n'
        f'|<b> Срок наказания:</b> {muteint} {mutetype}\n'
        f'|<b> Причина:</b> {comment}'
    )
    else:
        await message.reply("Некорректный формат времени. Пожалуйста, используйте 'м', 'ч' или 'д'.")



async def moder_stats(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("group_id")
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    user_id = call.from_user.id
    panelsend, panelsend_moder = await create_panelsend_markup(user_id)
    try:
        await cursor.execute("SELECT * FROM banned_users WHERE group_id=?", (group_id,))
        banned_users = await cursor.fetchall()
        if not banned_users:
            await call.message.edit_text("В этой группе нет заблокированных пользователей.", reply_markup=home_menu)
        else:
            await call.message.answer("Перешлите сообщение @имя или id пользователя, чтобы узнать больше информации.", reply_markup=panelsend_moder)
            await ModerationState.waiting_for_user_info.set()
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()



async def get_user_info(message: types.Message):
    user_id = None
    if message.forward_from:
        user_id = message.forward_from.id
    elif message.text.isdigit():
        user_id = message.text

    if user_id:
        conn = await aiosqlite.connect('my_db.db')
        cursor = await conn.cursor()
        try:
            await cursor.execute("SELECT * FROM banned_users WHERE user_id=?", (user_id,))
            user_info = await cursor.fetchone()
            if not user_info:
                await message.answer("Пользователь не заблокирован.")
                return
            user_id, banned_by_id, ban_time, group_id, reason = user_info

            user_info = await bot.get_chat_member(group_id, user_id)
            user_name = user_info.user.first_name

            admin_info = await bot.get_chat_member(group_id, banned_by_id)
            admin_name = admin_info.user.first_name

            response = f"Пользователь: <b>{user_name}</b> | id: <code>{user_id}</code>\nЗаблокировал: <b>{admin_name}</b> | id: <code>{banned_by_id}</code>\nВремя блокировки: <code>{ban_time}</code>\nГруппа: <b>{group_id}</b>\nПричина: <code>{reason}</code>\n\n"
            await message.answer(response, reply_markup=home_menu)
        finally:
            if cursor:
                await cursor.close()
            if conn:
                await conn.close()
    else:
        await message.answer("Пожалуйста, введите id пользователя или перешлите сообщение от пользователя.")


def register_handlers_moderator(dp: Dispatcher):
    dp.register_message_handler(mute, commands=['mute'])
    dp.register_callback_query_handler(moder_stats, text='moderation', state='*')
    dp.register_message_handler(get_user_info, state=ModerationState.waiting_for_user_info)
