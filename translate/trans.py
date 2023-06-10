from loader import *
from config import *
from data.db import *
from handlers.other_hand import set_default_command, set_start_admin


conn = sq.connect('my_db.db')
cursor = conn.cursor()


async def language_keyboard():
    markup = InlineKeyboardMarkup()
    keys = list(LANGDICT.keys())
    for i in range(0, len(keys), 2):
        row_btns = [
            InlineKeyboardButton(
                text=LANGDICT[keys[i]],
                callback_data=f"lang:{keys[i]}"
            ),
            InlineKeyboardButton(
                text=LANGDICT[keys[i+1]],
                callback_data=f"lang:{keys[i+1]}"
            ) if i+1 < len(keys) else None
        ]
        markup.row(*filter(None, row_btns))
    return markup


async def cmd_translate(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    data = await state.get_data()
    cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
    user_language_db = cursor.fetchone()
    user_language = user_language_db[0]
    data['lang'] = user_language
    text = await translate_text("Выбери язык", user_language)
    await bot.send_message(message.from_user.id, text, reply_markup=await language_keyboard())


async def process_callback_language(call: types.CallbackQuery):
    code = call.data.split(':')[-1]
    user_id = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users_interaction SET language = ? WHERE user_id = ?",
            (code, user_id)
        )
        conn.commit()
    await call.answer(await translate_text("Язык успешно изменен", code))
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
    user_language_db = cursor.fetchone()
    user_language = user_language_db[0]
    await set_default_command(dp, call.message.chat.id, user_language)
    await set_start_admin(dp, call.message.chat.id, user_id, user_language)
    return code


def register_handlers_language(dp: Dispatcher):
    dp.register_message_handler(cmd_translate, commands=['language'], state='*')
    dp.register_callback_query_handler(process_callback_language, lambda c: c.data and c.data.startswith('lang:'))
