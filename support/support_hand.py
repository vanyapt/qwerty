from loader import *
from config import *
from buttons.support_markup import *


async def cmd_support(message: types.Message):
    now = datetime.now().time()
    if time(6, 0) <= now <= time(22, 0):
        text = "Если вы хотите обратиться к владельцу бота нажмите на кнопку ниже"
        keyboard = await support_keyboard(messages="many")
        if not keyboard:
            await message.answer("К сожалению, сейчас владелец бота уже введет переписку. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
            return
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("Вы можете обратиться в поддержку с 6 утра по 22:00")


async def send_to_support_call(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.message.edit_text("Вы обратились к владельцу бота. Ждите ответа!")
    user_id = int(callback_data.get("user_id"))
    if not await check_support_available(user_id):
        support_id = await get_support_manager()
    else:
        support_id = user_id

    if not support_id:
        await call.message.edit_text("К сожалению, сейчас владелец бота уже введет переписку. Попробуйте позже.")
        await state.reset_state()
        return

    await state.set_state("wait_in_support")
    await state.update_data(second_id=support_id)

    keyboard = await support_keyboard(messages="many", user_id=call.from_user.id)

    await bot.send_message(support_id, f"С вами хочет связаться пользователь {call.from_user.full_name}, его id: {user_id}",reply_markup=keyboard)


async def answer_support_call(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    second_id = int(callback_data.get("user_id"))
    user_state = dp.current_state(user=second_id, chat=second_id)

    if str(await user_state.get_state()) != "wait_in_support":
        await call.message.edit_text("К сожалению, пользователь уже передумал.")
        return

    await state.set_state("in_support")
    await user_state.set_state("in_support")

    await state.update_data(second_id=second_id)

    keyboard = cancel_support(second_id)
    keyboard_second_user = cancel_support(call.from_user.id)

    await call.message.edit_text("Вы на связи с пользователем!\n""Чтобы завершить общение нажмите на кнопку.", reply_markup=keyboard)
    message = await bot.send_message(second_id, "Владелец бота на связи! Можете писать сюда свое сообщение.\n\n""Чтобы завершить общение нажмите на кнопку.", reply_markup=keyboard_second_user)
    await bot.pin_chat_message(message.chat.id, message.message_id)


async def not_supported(message: types.Message, state: FSMContext):
    data = await state.get_data()
    second_id = data.get("second_id")

    keyboard = cancel_support(second_id)
    await message.answer("Дождитесь ответа владелеца бота или отмените сеанс", reply_markup=keyboard)


async def exit_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user_id = int(callback_data.get("user_id"))
    second_state = dp.current_state(user=user_id, chat=user_id)

    if await second_state.get_state() is not None:
        data_second = await second_state.get_data()
        second_id = data_second.get("second_id")
        if int(second_id) == int(call.from_user.id):
            await second_state.reset_state()
            await bot.send_message(user_id, "Сеанс был завершен")

    data = await state.get_data()
    message_id = data.get("message_id")

    await call.message.edit_text("Вы завершили сеанс")
    await state.reset_state()
    await bot.unpin_chat_message(call.message.chat.id, message_id)


def register_handlers_support(dp: Dispatcher):
    dp.register_message_handler(cmd_support, commands=['support'])
    dp.register_callback_query_handler(send_to_support_call, support_callback.filter(messages="many", as_user="yes"))
    dp.register_callback_query_handler(answer_support_call, support_callback.filter(messages="many", as_user="no"))
    dp.register_message_handler(not_supported, state="wait_in_support", content_types=types.ContentTypes.ANY)
    dp.register_callback_query_handler(exit_support, cancel_support_callback.filter(), state=["in_support", "wait_in_support", None])
