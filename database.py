import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('salon.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS masters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT,
                name_en TEXT,
                name_kz TEXT,
                specialization TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        try:
            self.cursor.execute("SELECT name_kz FROM masters LIMIT 1")
        except sqlite3.OperationalError:
            self.cursor.execute("ALTER TABLE masters ADD COLUMN name_kz TEXT")
            print("✅ Добавлена колонка name_kz в таблицу masters")
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT,
                name_en TEXT,
                name_kz TEXT,
                price_from INTEGER,
                price_to INTEGER,
                duration INTEGER,
                category TEXT
            )
        ''')
        
        try:
            self.cursor.execute("SELECT name_kz FROM services LIMIT 1")
        except sqlite3.OperationalError:
            self.cursor.execute("ALTER TABLE services ADD COLUMN name_kz TEXT")
            print("✅ Добавлена колонка name_kz в таблицу services")
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                user_phone TEXT,
                master_id INTEGER,
                service_id INTEGER,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'pending',
                language TEXT DEFAULT 'ru',
                created_at TEXT,
                notes TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                master_id INTEGER,
                note TEXT,
                is_blocked INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
        self.add_initial_data()
    
    def add_initial_data(self):
        masters = [
            (1, 'Анна', 'Anna', 'Анна', 'Стрижки, окрашивание'),
            (2, 'Елена', 'Elena', 'Елена', 'Маникюр, педикюр'),
            (3, 'Мария', 'Maria', 'Мария', 'Шугаринг, макияж'),
            (4, 'Дарья', 'Daria', 'Дария', 'Стрижки, укладки')
        ]
        
        for m in masters:
            self.cursor.execute('''
                INSERT OR IGNORE INTO masters (id, name_ru, name_en, name_kz, specialization)
                VALUES (?, ?, ?, ?, ?)
            ''', m)
        
        services = [
            (1, 'Стрижка женская', "Women's haircut", 'Әйелдерге шаш қию', 30, 60, 60, 'hair'),
            (2, 'Стрижка мужская', "Men's haircut", 'Ерлерге шаш қию', 20, 40, 40, 'hair'),
            (3, 'Маникюр', 'Manicure', 'Маникюр', 25, 50, 60, 'nails'),
            (4, 'Педикюр', 'Pedicure', 'Педикюр', 35, 70, 90, 'nails'),
            (5, 'Шугаринг', 'Sugaring', 'Шугаринг', 20, 80, 60, 'hair_removal'),
            (6, 'Макияж', 'Makeup', 'Макияж', 30, 100, 60, 'makeup'),
            (7, 'Окрашивание', 'Hair coloring', 'Шаш бояу', 50, 150, 120, 'hair'),
            (8, 'Укладка', 'Styling', 'Шаш сәндеу', 20, 40, 40, 'hair')
        ]
        
        for s in services:
            self.cursor.execute('''
                INSERT OR IGNORE INTO services (id, name_ru, name_en, name_kz, price_from, price_to, duration, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', s)
        
        self.conn.commit()
        print("✅ Начальные данные добавлены")
    
    def get_masters(self, lang='ru'):
        if lang == 'ru':
            name_field = 'name_ru'
        elif lang == 'en':
            name_field = 'name_en'
        else:
            name_field = 'name_kz'
            
        self.cursor.execute(f'''
            SELECT id, {name_field}, specialization FROM masters WHERE is_active = 1
        ''')
        return self.cursor.fetchall()
    
    def get_services(self, lang='ru'):
        if lang == 'ru':
            name_field = 'name_ru'
        elif lang == 'en':
            name_field = 'name_en'
        else:
            name_field = 'name_kz'
            
        self.cursor.execute(f'''
            SELECT id, {name_field}, price_from, price_to FROM services ORDER BY category
        ''')
        return self.cursor.fetchall()
    
    def get_service(self, service_id, lang='ru'):
        if lang == 'ru':
            name_field = 'name_ru'
        elif lang == 'en':
            name_field = 'name_en'
        else:
            name_field = 'name_kz'
            
        self.cursor.execute(f'''
            SELECT {name_field}, price_from, price_to, duration FROM services WHERE id = ?
        ''', (service_id,))
        return self.cursor.fetchone()
    
    def get_master(self, master_id, lang='ru'):
        if lang == 'ru':
            name_field = 'name_ru'
        elif lang == 'en':
            name_field = 'name_en'
        else:
            name_field = 'name_kz'
            
        self.cursor.execute(f'''
            SELECT {name_field}, specialization FROM masters WHERE id = ?
        ''', (master_id,))
        return self.cursor.fetchone()
    
    def get_booked_slots(self, date, master_id):
        self.cursor.execute('''
            SELECT time FROM appointments 
            WHERE date = ? AND master_id = ? AND status != 'cancelled'
        ''', (date, master_id))
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_admin_notes(self, date, master_id):
        self.cursor.execute('''
            SELECT time, note, is_blocked FROM admin_notes 
            WHERE date = ? AND master_id = ?
        ''', (date, master_id))
        return self.cursor.fetchall()
    
    def add_admin_note(self, date, time, master_id, note, is_blocked=0):
        self.cursor.execute('''
            INSERT INTO admin_notes (date, time, master_id, note, is_blocked)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, time, master_id, note, is_blocked))
        self.conn.commit()
    
    def update_admin_note(self, date, time, master_id, new_note):
        self.cursor.execute('''
            UPDATE admin_notes SET note = ? WHERE date = ? AND time = ? AND master_id = ?
        ''', (new_note, date, time, master_id))
        self.conn.commit()
    
    def delete_admin_note(self, date, time, master_id):
        self.cursor.execute('''
            DELETE FROM admin_notes WHERE date = ? AND time = ? AND master_id = ?
        ''', (date, time, master_id))
        self.conn.commit()
    
    def create_appointment(self, user_id, user_name, user_phone, master_id, service_id, date, time, lang='ru'):
        self.cursor.execute('''
            INSERT INTO appointments (user_id, user_name, user_phone, master_id, service_id, date, time, language, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, user_phone, master_id, service_id, date, time, lang, datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_appointments(self, date=None, master_id=None):
        query = "SELECT * FROM appointments WHERE 1=1"
        params = []
        
        if date:
            query += " AND date = ?"
            params.append(date)
        if master_id:
            query += " AND master_id = ?"
            params.append(master_id)
        
        query += " ORDER BY date, time"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def update_appointment_status(self, appointment_id, status):
        self.cursor.execute('''
            UPDATE appointments SET status = ? WHERE id = ?
        ''', (status, appointment_id))
        self.conn.commit()
    
    def close(self):
        self.conn.close()