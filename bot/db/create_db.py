# from .base_db import begin_conn


# Создание таблиц в базе данных
async def create_tables():
    with begin_conn() as conn:
        cursor = conn.cursor()
        # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS users (
        #     chat_id BIGINT PRIMARY KEY,
        #     agreed BOOLEAN,
        #     role TEXT,
        #     fio TEXT,
        #     inn TEXT,
        #     title TEXT,
        #     juridical_type TEXT,
        #     ord_id INTEGER,
        #     balance DECIMAL(10, 2) DEFAULT 0.00,
        #     total_balance DECIMAL(10, 2) DEFAULT 0.00
        # )
        # ''')
        # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS platforms (
        #     id SERIAL PRIMARY KEY,
        #     chat_id INTEGER,
        #     platform_name TEXT,
        #     platform_url TEXT,
        #     advertiser_link TEXT,
        #     average_views INTEGER,
        #     link TEXT,
        #     ord_id TEXT,
        #     vat_included TEXT
        # )
        # ''')
        # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS contracts (
        #     id SERIAL PRIMARY KEY,
        #     chat_id INTEGER,
        #     contractor_id BIGINT,
        #     contract_date TEXT,
        #     end_date TEXT,
        #     serial TEXT,
        #     amount REAL,
        #     vat_included INTEGER,
        #     ord_id TEXT
        # )
        # ''')
        cursor.execute('''
        # CREATE TABLE IF NOT EXISTS ad_campaigns (
        #     id SERIAL PRIMARY KEY,
        #     chat_id BIGINT,
        #     campaign_id TEXT,
        #     brand TEXT,
        #     service TEXT,
        #     ord_id TEXT
        # )
        # ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS target_links (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            campaign_id TEXT,
            link TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            file_type TEXT,
            original_path TEXT,
            resized_path TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS creatives (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            campaign_id TEXT,
            creative_id TEXT,
            content_type TEXT,
            content TEXT,
            token TEXT,
            ord_id TEXT,
            status TEXT DEFAULT 'pending'
        )
        ''')
        # Добавление таблицы для оплаты
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            inv_id TEXT,
            amount DECIMAL,
            status TEXT
        )
        ''')
        # Добавление таблицы user_creatives
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS user_creatives (
                        id SERIAL PRIMARY KEY,
                       chat_id BIGINT,
                       creatives TEXT
                   )
               """)

        # Добавление таблицы user_state
        cursor.execute("""
                   CREATE TABLE IF NOT EXISTS user_state (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT,
                        current_campaign BIGINT
                   )
               """)

        # Добавление таблицы creatives
        # cursor.execute("""
        #            CREATE TABLE IF NOT EXISTS creatives (
        #                id SERIAL PRIMARY KEY,
        #                chat_id BIGINT,
        #                campaign_id BIGINT,
        #                type TEXT,
        #                content TEXT,
        #                resized_path TEXT
        #            )
        #        """)

        # Добавление таблицы creative_links
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creative_links (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                link TEXT,
                ord_id TEXT,
                creative_id TEXT,
                token TEXT
            )
        """)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selected_contractors (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                contractor_id BIGINT
            )
            ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            link TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            reminder_time TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            campaign_id TEXT,
            creative_id TEXT,
            platform_url TEXT,
            views INTEGER,
            date_start_actual DATE
        )
        ''')
        # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS contractors (
        #     id SERIAL PRIMARY KEY,
        #     chat_id BIGINT,
        #     contractor_id BIGINT,
        #     fio TEXT,
        #     title TEXT,
        #     inn TEXT,
        #     juridical_type TEXT,
        #     role TEXT,
        #     ord_id TEXT
        # )
        # ''')
        # cursor.execute('''
        #        CREATE TABLE IF NOT EXISTS payment_yk (
        #             id SERIAL PRIMARY KEY,
        #             created_at TIMESTAMP DEFAULT NOW(),
        #             user_id BIGINT,
        #             pay_id VARCHAR(255),
        #             card VARCHAR(255)
        #         );
        #        ''')
        conn.commit()
        cursor.close()
