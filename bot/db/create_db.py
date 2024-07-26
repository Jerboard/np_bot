from .base_db import begin_conn


# Создание таблиц в базе данных
def create_tables():
    with begin_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            agreed BOOLEAN,
            role TEXT,
            fio TEXT,
            inn TEXT,
            title TEXT,
            juridical_type TEXT,
            ord_id INTEGER,
            balance DECIMAL(10, 2) DEFAULT 0.00,
            total_balance DECIMAL(10, 2) DEFAULT 0.00
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS platforms (
            chat_id INTEGER,
            platform_name TEXT,
            platform_url TEXT,
            advertiser_link TEXT,
            average_views INTEGER,
            link TEXT,
            ord_id TEXT,
            vat_included TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            chat_id INTEGER,
            contractor_id INTEGER,
            contract_date TEXT,
            end_date TEXT,
            serial TEXT,
            amount REAL,
            vat_included INTEGER,
            ord_id TEXT,
            PRIMARY KEY (chat_id, contractor_id, ord_id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            chat_id INTEGER,
            campaign_id TEXT,
            brand TEXT,
            service TEXT,
            ord_id TEXT,
            PRIMARY KEY (chat_id, campaign_id, ord_id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS target_links (
            chat_id INTEGER,
            campaign_id TEXT,
            link TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            chat_id INTEGER,
            file_type TEXT,
            original_path TEXT,
            resized_path TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS creatives (
            chat_id INTEGER,
            campaign_id TEXT,
            creative_id TEXT,
            content_type TEXT,
            content TEXT,
            token TEXT,
            ord_id INTEGER,
            status TEXT DEFAULT 'pending',
            PRIMARY KEY (chat_id, campaign_id, creative_id, ord_id)
        )
        ''')
        # Добавление таблицы для оплаты
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            chat_id INTEGER,
            inv_id TEXT,
            amount DECIMAL,
            status TEXT,
            PRIMARY KEY (chat_id, inv_id)
        )
        ''')
        # Добавление таблицы user_creatives
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS user_creatives (
                       chat_id INTEGER PRIMARY KEY,
                       creatives TEXT
                   )
               """)

        # Добавление таблицы user_state
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS user_state (
                       chat_id INTEGER PRIMARY KEY,
                       current_campaign INTEGER
                   )
               """)

        # Добавление таблицы creatives
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS creatives (
                       id SERIAL PRIMARY KEY,
                       chat_id INTEGER,
                       campaign_id INTEGER,
                       type TEXT,
                       content TEXT,
                       resized_path TEXT
                   )
               """)

        # Добавление таблицы creative_links
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creative_links (
                chat_id INTEGER,
                link TEXT,
                ord_id TEXT,
                creative_id TEXT,
                token TEXT
            )
        """)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selected_contractors (
                chat_id INTEGER,
                contractor_id INTEGER
            )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            chat_id INTEGER,
            link TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            chat_id INTEGER,
            reminder_time TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            chat_id INTEGER,
            campaign_id TEXT,
            creative_id TEXT,
            platform_url TEXT,
            views INTEGER,
            date_start_actual DATE
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contractors (
            chat_id INTEGER PRIMARY KEY,
            contractor_id INTEGER,
            fio TEXT,
            title TEXT,
            inn TEXT,
            juridical_type TEXT,
            role TEXT,
            ord_id TEXT
        )
        ''')
        conn.commit()
        cursor.close()

# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS creatives (
#         id SERIAL PRIMARY KEY,
#         chat_id INTEGER,
#         campaign_id INTEGER,
#         type TEXT,
#         content TEXT,
#         resized_path TEXT
#     )
# """)
