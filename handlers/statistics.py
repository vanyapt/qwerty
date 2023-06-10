from loader import *
from config import *
from buttons.admin_kb import *
import matplotlib.pyplot as plt


async def process_stats(call: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    chat_id_user = call.from_user.id
    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (chat_id_user,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
    data = await state.get_data()
    group_id = data.get("group_id")
    chat_id = group_id
    chat = await bot.get_chat(group_id)
    chat_name = chat.title
    chat_administrators = await bot.get_chat_administrators(chat_id)
    admin_names = []
    sk = await translate_text("скрыт", user_language)
    for i, admin in enumerate(chat_administrators):
        if admin.user.first_name:
            full_name = admin.user.first_name
            if admin.user.last_name:
                full_name += " " + admin.user.last_name
            if admin.user.is_bot:
                admin_role = await translate_text("Бот", user_language)
            else:
                admin_role = await translate_text("Админ", user_language)

            admin_names.append((str(i+1), admin_role, full_name, "@"+admin.user.username if admin.user.username else sk, str(admin.user.id)))
        else:
            admin_names.append((str(i+1), "Админ", sk, "", str(admin.user.id)))
    role = await translate_text("Роль", user_language)
    nam = await translate_text("Имя", user_language)
    name_use = await translate_text("Имя пользователя", user_language)
    admin_names.insert(0, ("№", role, nam, name_use, "id"))
    cell_padding = 50
    max_widths = [0, 0, 0, 0, 0]
    for row in admin_names:
        for i, value in enumerate(row):
            text_width = len(str(value)) * 20
            if text_width > max_widths[i]:
                max_widths[i] = text_width
    cell_widths = [w + cell_padding for w in max_widths]
    cell_height = int(1.3 * 40)
    x_offset = 20
    y_offset = 90
    image_width = math.ceil(x_offset * 2 + sum(cell_widths))
    image_height = math.ceil(y_offset * 2 + cell_height * len(admin_names))
    image = Image.new('RGB', (image_width, image_height), color=(71, 147, 227))
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype('calibri.ttf', 60)
    title_text = await translate_text('Администраторы канала', user_language)
    title_width, _ = draw.textsize(title_text, font=title_font)
    x_title = math.ceil((image_width - title_width) / 2)
    y_title = y_offset - 80
    draw.text((x_title, y_title), title_text, font=title_font, fill=(255, 255, 255))
    admin_font = ImageFont.truetype('calibri.ttf', 30)
    data_color_1 = (240, 240, 240)
    data_color_2 = (250, 250, 250)
    for i, admin in enumerate(admin_names):
        for j, value in enumerate(admin):
            cell_x = x_offset + sum(cell_widths[:j])
            cell_y = y_offset + i * cell_height
            draw.rectangle((cell_x, cell_y, cell_x + cell_widths[j], cell_y + cell_height), outline=(255, 0, 0), width=1)
            if i == 0:
                font = admin_font
                if value in ("№", nam, "id"):
                    fill_color = (50, 73, 96)
                else:
                    fill_color = (79, 195, 161)
                text_color = (255, 255, 255)
            else:
                font = admin_font
                if i % 2 == 1:
                    fill_color = data_color_1
                else:
                    fill_color = data_color_2
                if value in ("№", nam, "id"):
                    text_color = (255, 255, 255)
                else:
                    text_color = (0, 0, 0)
            if value is None:
                continue
            text = str(value)
            text_width, _ = draw.textsize(text, font=font)
            text_x = cell_x + (cell_widths[j] - text_width) // 2
            text_y = cell_y + cell_height // 2
            draw.rectangle((cell_x, cell_y, cell_x + cell_widths[j], cell_y + cell_height), fill=fill_color)
            draw.text((text_x, text_y), text, font=font, fill=text_color, anchor='lm')
    img_buffer = BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    members_count = await bot.get_chat_members_count(chat_id)
    sub = await translate_text("Подписчиков", user_language)
    await bot.send_photo(call.message.chat.id, caption=f"<b>{chat_name}</b> | {sub}: <b>{members_count}</b>\n", photo=img_buffer, reply_markup=home_menu)


async def stat_interaction(call: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    user_id = call.from_user.id

    with sq.connect('my_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users_interaction WHERE user_id = ?", (user_id,))
        user_language_db = cursor.fetchone()
        user_language = user_language_db[0]
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users_interaction")
        total_users = cursor.fetchone()[0]

        today = datetime.today().date()
        seven_days_ago = today - timedelta(days=6)
        thirty_days_ago = today - timedelta(days=30)

        cursor.execute(f"SELECT COUNT(*) FROM users_interaction WHERE DATE(first_interaction) = '{today}'")
        new_users_today = cursor.fetchone()[0]
        cursor.execute(f"SELECT DATE(first_interaction) as date, COUNT(*) as count FROM users_interaction WHERE DATE(first_interaction) >= '{seven_days_ago}' GROUP BY date")
        first_interaction_counts = cursor.fetchall()
        cursor.execute(f"SELECT DATE(first_interaction) as date, COUNT(*) as count FROM users_interaction WHERE DATE(first_interaction) >= '{thirty_days_ago}' GROUP BY date")
        first_interaction_counts_month = cursor.fetchall()
        cursor.execute(f"SELECT DATE(last_interaction) as date, COUNT(*) as count FROM users_interaction WHERE DATE(last_interaction) >= '{seven_days_ago}' GROUP BY date")
        last_interaction_counts = cursor.fetchall()

    all_dates = [seven_days_ago + timedelta(days=i) for i in range(7)]
    default_counts = {date.strftime("%Y-%m-%d"): 0 for date in all_dates}

    first_interaction_counts = {**default_counts, **{date: count for date, count in first_interaction_counts}}
    first_interaction_counts_month = {**default_counts, **{date: count for date, count in first_interaction_counts_month}}
    last_interaction_counts = {**default_counts, **{date: count for date, count in last_interaction_counts}}

    new_user_dates = [datetime.strptime(date, "%Y-%m-%d") for date in first_interaction_counts.keys()]
    new_user_counts = list(first_interaction_counts.values())
    new_user_counts_month = list(first_interaction_counts_month.values())
    last_user_dates = [datetime.strptime(date, "%Y-%m-%d") for date in last_interaction_counts.keys()]
    last_user_counts = list(last_interaction_counts.values())
    total_new_users = sum(new_user_counts)
    total_new_users_month = sum(new_user_counts_month)
    week_percentage = round((total_new_users / total_users) * 100, 2)
    month_percentage = round((total_new_users_month / total_users) * 100, 2)

    fig, ax = plt.subplots(figsize=(25.6, 14.4), dpi=80)
    ns = await translate_text('Новые пользователи', user_language)
    la = await translate_text('Последняя активность', user_language)
    width = 0.4
    new_user_dates = [date - timedelta(days=width/2) for date in new_user_dates]
    last_user_dates = [date + timedelta(days=width/2) for date in last_user_dates]

    ax.bar(new_user_dates, new_user_counts, width=width, label=ns, color='tab:blue')
    ax.bar(last_user_dates, last_user_counts, width=width, label=la, color='tab:orange')

    ax.set_ylabel('', color='gray', fontsize=28, labelpad=10)
    bot_info = await bot.get_me()
    bot_name = bot_info.username
    act = await translate_text("Активность в", user_language)
    nd = await translate_text("за последнюю неделю", user_language)
    ax.set_title(f'{act} @{bot_name} {nd}', pad=40, color='black', fontsize=30)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.grid(color='gray', linestyle='solid')
    ax.legend(loc='upper left', fontsize=28)
    plt.xticks(all_dates, rotation=45, color='gray', fontsize=28)
    ax.tick_params(axis='y', labelsize=28)
    max_count = max(max(new_user_counts + last_user_counts), 5)
    y_ticks = np.linspace(0, max_count, num=5, dtype=int)
    if max_count <= 5:
        y_ticks = list(range(0, max_count + 1))
    ax.set_yticks(y_ticks)
    date_format = "%Y-%m-%d"
    date_formatter = DateFormatter(date_format)
    ax.xaxis.set_major_formatter(date_formatter)
    plt.subplots_adjust(left=0.10, right=0.90, top=0.90, bottom=0.30)

    all = await translate_text("Все пользователи", user_language)
    td = await translate_text("За сегодня", user_language)
    d7 = await translate_text("За последние 7 дней", user_language)
    lm = await translate_text("За последний месяц", user_language)
    message = (
        f"{all}: {total_users}\n"
        f"{td}: {new_users_today}\n"
        f"{d7}: {total_new_users} +{week_percentage}%\n"
        f"{lm}: {total_new_users_month} +{month_percentage}%"
    )
    with BytesIO() as buf:
        plt.savefig(buf, format='png', dpi=200)
        buf.seek(0)
        await bot.send_photo(chat_id = call.from_user.id, caption=message, photo=buf)


def register_handlers_statistics(dp: Dispatcher):
    dp.register_callback_query_handler(process_stats, text='stats', state='*')
    dp.register_callback_query_handler(stat_interaction, text='stats_bot', state='*')
