from loader import *
import sqlite3 as sq
import aiosqlite

async def create_db():
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS my_group
                    (id_group TEXT PRIMARY KEY,
                     id_admin TEXT)
                   """)
    conn.commit()
    cursor.close()
    conn.close()


async def create_db_post():
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS my_post
        (id_post INTEGER PRIMARY KEY,
        publish_time DATETIME NOT NULL,
        file TEXT,
        file_type TEXT,
        text TEXT,
        url_buttons TEXT,
        message_id INTEGER,
        id_group TEXT NOT NULL)
        """)

    conn.commit()
    cursor.close()
    conn.close()


async def create_url_buttons():
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""CREATE TABLE IF NOT EXISTS buttons
            (id INTEGER PRIMARY KEY,
            text TEXT,
            url TEXT,
            id_post INTEGER,
            FOREIGN KEY(id_post) REFERENCES my_post(id_post) ON DELETE CASCADE)
            """)
    conn.commit()
    cursor.close()
    conn.close()


async def setting_admin():
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS setting
            (id_admin TEXT PRIMARY KEY,
            disable_web_page_preview BOOLEAN DEFAULT 0,
            disable_notification BOOLEAN DEFAULT 1,
            new_left_chat BOOLEAN DEFAULT 0)
            """)

    conn.commit()
    cursor.close()
    conn.close()


async def create_banned_users_table():
    conn = await aiosqlite.connect('my_db.db')
    cursor = await conn.cursor()

    await cursor.execute("PRAGMA foreign_keys = ON")

    await cursor.execute("""CREATE TABLE IF NOT EXISTS banned_users
        (user_id INTEGER,
        banned_by_id INTEGER,
        ban_time TEXT,
        group_id TEXT,
        ban_reason TEXT,
        PRIMARY KEY(user_id, group_id))
        """)

    await conn.commit()
    await cursor.close()
    await conn.close()

async def setting_interaction():
    conn = sq.connect('my_db.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users_interaction
            (user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            first_interaction DATETIME,
            last_interaction DATETIME,
            language TEXT DEFAULT 'uk')
            """)

    conn.commit()
    cursor.close()
    conn.close()
