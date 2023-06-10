from loader import *
from aiogram import executor
from handlers import client_hand, admin_hand, other_hand, super_admin, statistics
from handlers.other_hand import publish_post
from support import support_hand
from support.support_chat import SupportMiddleware
from chat_moderator import admin_chat
from translate import trans
from data.db import create_db_post, create_url_buttons, setting_interaction, create_db


async def on_startup(dp):
    await create_db()
    await create_db_post()
    await create_url_buttons()
    await setting_interaction()
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()
    missed_posts = 0
    first_missed_post_time = None
    try:
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='my_post'")
        result = await cursor.fetchone()
        if result:
            await cursor.execute("SELECT id_post, publish_time, message_id FROM my_post")
            posts = await cursor.fetchall()
            for post in posts:
                id_post, publish_time_str, message_id = post
                publish_time = datetime.strptime(publish_time_str, "%Y-%m-%d %H:%M:%S")
                time_elapsed = datetime.now() - publish_time
                if time_elapsed > timedelta(hours=48) and message_id is None:
                    await cursor.execute("DELETE FROM my_post WHERE id_post=?", (id_post,))
                    missed_posts += 1
                    if first_missed_post_time is None or publish_time < first_missed_post_time:
                        first_missed_post_time = publish_time
                elif datetime.now() > publish_time:
                    missed_posts += 1
                    if first_missed_post_time is None or publish_time < first_missed_post_time:
                        first_missed_post_time = publish_time
                else:
                    asyncio.create_task(publish_post(id_post, publish_time))
            await conn.commit()
            if missed_posts > 0:
                print(f"{missed_posts} публикации не публиковались. Первая пропущенная публикация должена была быть опубликована в {first_missed_post_time}.")
        else:
            print("Table 'my_post' does not exist.")
    finally:
        if cursor:
            await cursor.close()
        if conn:
            await conn.close()


other_hand.register_handlers_other(dp)
admin_hand.register_handlers_admin(dp)
client_hand.register_handlers_client(dp)
support_hand.register_handlers_support(dp)
super_admin.register_handlers_super_admin(dp)
admin_chat.register_handlers_moderator(dp)
statistics.register_handlers_statistics(dp)
trans.register_handlers_language(dp)


dp.middleware.setup(SupportMiddleware())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
