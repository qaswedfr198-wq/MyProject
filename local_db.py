import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")

class LocalBackend:
    def get_connection(self):
        return sqlite3.connect(DB_NAME)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Inventory Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit TEXT, -- Added unit column
                expiry_date TEXT,
                buy_date TEXT,
                area TEXT NOT NULL
            )
        ''')

        # Migration: Add unit column if not exists
        try:
            cursor.execute("ALTER TABLE inventory ADD COLUMN unit TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column likely already exists
            pass
        
        # Family Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                allergens TEXT,
                genetic_conditions TEXT,
                height REAL,
                weight REAL
            )
        ''')
        
        # Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER,
                key TEXT,
                value TEXT,
                PRIMARY KEY (user_id, key)
            )
        ''')

        # Quick Replies Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        ''')

        # Chat History Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Daily Recipes Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        ''')

        # Kitchen Equipment Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kitchen_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_name TEXT UNIQUE NOT NULL
            )
        ''')

        # Calorie Records Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                food_name TEXT NOT NULL,
                calories INTEGER NOT NULL,
                note TEXT
            )
        ''')

        # Shopping List Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopping_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT NOT NULL,
                quantity TEXT, 
                is_checked INTEGER DEFAULT 0,
                unit TEXT
            )
        ''')
        
        # Migrate existing tables for user_isolation
        migration_targets = ["inventory", "family", "settings", "quick_replies", "chat_history", "daily_recipes", "kitchen_equipment"]
        for table in migration_targets:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
            except sqlite3.OperationalError:
                pass
            
            # Default NULL user_id to 0 for local compatibility
            cursor.execute(f"UPDATE {table} SET user_id = 0 WHERE user_id IS NULL")
        
        # Standardize family column names and settings
        try:
            cursor.execute("ALTER TABLE family ADD COLUMN genetic_conditions TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("UPDATE family SET genetic_conditions = genetic WHERE genetic_conditions IS NULL")
        except:
            pass
        
        conn.commit()
        conn.close()

    # --- Inventory Operations ---
    def add_inventory_item(self, user_id, name, quantity, unit, expiry_date, buy_date, area):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check existing item
        cursor.execute("SELECT id, quantity, expiry_date, buy_date FROM inventory WHERE name = ? AND area = ? AND user_id = ? AND unit IS ?", (name, area, user_id, unit))
        existing = cursor.fetchone()
        
        if existing:
            item_id, old_qty, old_expiry_date, old_buy_date = existing
            new_qty = old_qty + quantity
            final_expiry_date = min(old_expiry_date, expiry_date)
            final_buy_date = min(old_buy_date, buy_date)
            
            cursor.execute('''
                UPDATE inventory 
                SET quantity = ?, expiry_date = ?, buy_date = ?
                WHERE id = ? AND user_id = ?
            ''', (new_qty, final_expiry_date, final_buy_date, item_id, user_id))
        else:
            cursor.execute('''
                INSERT INTO inventory (user_id, name, quantity, unit, expiry_date, buy_date, area)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, quantity, unit, expiry_date, buy_date, area))
            
        conn.commit()
        conn.close()

    def update_item_quantity(self, user_id, item_id, delta):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE id = ? AND user_id = ?", (delta, item_id, user_id))
        conn.commit()
        conn.close()

    def get_items_by_area(self, user_id, area):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        # Explicit SELECT to match remote_db signature (id, name, qty, unit, expiry, buy, area)
        cursor.execute("SELECT id, name, quantity, unit, expiry_date, buy_date, area FROM inventory WHERE area = ? AND user_id = ?", (area, user_id))
        items = cursor.fetchall()
        conn.close()
        return items

    def get_all_inventory(self, user_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, name, quantity, unit, expiry_date, buy_date, area FROM inventory WHERE user_id = ?", (user_id,))
        items = cursor.fetchall()
        conn.close()
        return items

    def delete_inventory_item(self, user_id, item_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = ? AND user_id = ?", (item_id, user_id))
        conn.commit()
        conn.close()

    def update_inventory_item(self, user_id, item_id, name=None, quantity=None, unit=None, expiry_date=None, buy_date=None, area=None):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        if unit is not None:
            updates.append("unit = ?")
            params.append(unit)
        if expiry_date is not None:
            updates.append("expiry_date = ?")
            params.append(expiry_date)
        if buy_date is not None:
            updates.append("buy_date = ?")
            params.append(buy_date)
        if area is not None:
            updates.append("area = ?")
            params.append(area)
            
        if not updates:
            conn.close()
            return
            
        sql = f"UPDATE inventory SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        params.extend([item_id, user_id])
        
        cursor.execute(sql, params)
        conn.commit()
        conn.close()

    # --- Family Operations ---
    def add_family_member(self, user_id, name, age, gender, allergens, genetic, height, weight):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO family (user_id, name, gender, age, height, weight, allergens, genetic_conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, gender, age, height, weight, allergens, genetic))
        conn.commit()
        conn.close()

    def get_family_members(self, user_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM family WHERE user_id = ?", (user_id,))
        members = cursor.fetchall()
        conn.close()
        return members

    def update_family_member(self, user_id, member_id, name, age, gender, allergens, genetic, height, weight):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE family 
            SET name=?, gender=?, age=?, height=?, weight=?, allergens=?, genetic_conditions=?
            WHERE id=? AND user_id=?
        ''', (name, gender, age, height, weight, allergens, genetic, member_id, user_id))
        conn.commit()
        conn.close()

    def delete_family_member(self, user_id, member_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM family WHERE id = ? AND user_id = ?", (member_id, user_id))
        conn.commit()
        conn.close()

    # --- Settings Operations ---
    def get_setting(self, user_id, key):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ? AND user_id = ?", (key, user_id))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def set_setting(self, user_id, key, value):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)", (user_id, key, value))
        conn.commit()
        conn.close()

    # --- Quick Replies Operations ---
    def add_quick_reply(self, user_id, content):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quick_replies (user_id, content) VALUES (?, ?)", (user_id, content))
        conn.commit()
        conn.close()

    def get_quick_replies(self, user_id=None):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quick_replies WHERE user_id = ?", (user_id,))
        replies = cursor.fetchall()
        conn.close()
        return replies

    def delete_quick_reply(self, user_id, reply_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quick_replies WHERE id = ? AND user_id = ?", (reply_id, user_id))
        conn.commit()
        conn.close()

    # --- Chat History Operations ---
    def add_chat_message(self, user_id, sender, message):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (user_id, sender, message) VALUES (?, ?, ?)", (user_id, sender, message))
        conn.commit()
        conn.close()

    def get_chat_history(self, user_id, date_str=None):
        """
        Get chat history. If date_str is provided (YYYY-MM-DD), filter by date.
        """
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        if date_str:
            cursor.execute("SELECT sender, message, timestamp FROM chat_history WHERE user_id = ? AND date(timestamp) = ? ORDER BY timestamp ASC", (user_id, date_str))
        else:
            cursor.execute("SELECT sender, message, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
        history = cursor.fetchall()
        conn.close()
        return history

    def clear_chat_history(self, user_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def get_chat_dates(self, user_id):
        """
        Get a list of unique dates that have chat history.
        """
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date(timestamp) FROM chat_history WHERE user_id = ? ORDER BY date(timestamp) DESC", (user_id,))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates

    # --- Daily Recipe Operations ---
    def save_daily_recipes(self, user_id, date_str, content):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_recipes (user_id, date, content)
            VALUES (?, ?, ?)
        ''', (user_id, date_str, content))
        conn.commit()
        conn.close()

    def get_daily_recipes(self, user_id, date_str):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM daily_recipes WHERE user_id = ? AND date = ?", (user_id, date_str))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None

    # --- Kitchen Equipment Operations ---
    def get_kitchen_equipment(self, user_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT equipment_name FROM kitchen_equipment WHERE user_id = ?", (user_id,))
        equipment = [row[0] for row in cursor.fetchall()]
        conn.close()
        return equipment

    def update_kitchen_equipment(self, user_id, equipment_list):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kitchen_equipment WHERE user_id = ?", (user_id,))
        for name in equipment_list:
            cursor.execute("INSERT INTO kitchen_equipment (user_id, equipment_name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        conn.close()

    # --- Calorie Operations ---
    def add_calorie_record(self, user_id, date_str, meal_type, food_name, calories, note):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calories (user_id, date, meal_type, food_name, calories, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, date_str, meal_type, food_name, calories, note))
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    def get_calorie_records(self, user_id, date_str):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, meal_type, food_name, calories, note FROM calories WHERE user_id = ? AND date = ?", (user_id, date_str))
        records = cursor.fetchall()
        conn.close()
        return records

    def delete_calorie_record(self, user_id, record_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM calories WHERE id = ? AND user_id = ?", (record_id, user_id))
        conn.commit()
        conn.close()

    def get_daily_calorie_total(self, user_id, date_str):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(calories) FROM calories WHERE user_id = ? AND date = ?", (user_id, date_str))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else 0

    def get_daily_calorie_breakdown(self, user_id, date_str):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT meal_type, SUM(calories) FROM calories WHERE user_id = ? AND date = ? GROUP BY meal_type", (user_id, date_str))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_weekly_calorie_summary(self, user_id, end_date_str):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        # SQLite's date math: date(date_str, '-6 days') calculates the start date
        start_date_str = f"date('{end_date_str}', '-6 days')" 
        # Safer to just do it in python or rely on text comparison if format is YYYY-MM-DD
        
        cursor.execute(f'''
            SELECT date, SUM(calories) 
            FROM calories 
            WHERE user_id = ? AND date <= ? AND date >= date(?, '-6 days')
            GROUP BY date
        ''', (user_id, end_date_str, end_date_str))
        
        results = cursor.fetchall()
        conn.close()
        return results

    # --- Shopping List Operations ---
    def add_shopping_item(self, user_id, item_name, quantity, unit=""):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        # Check if item exists (unchecked), if so, maybe just update quantity? 
        # For simplicity, we'll allow duplicates or just add to existing.
        # Let's simple check if exists with same name and is_checked=0
        cursor.execute("SELECT id FROM shopping_list WHERE user_id = ? AND item_name = ? AND is_checked = 0", (user_id, item_name))
        existing = cursor.fetchone()
        
        if existing:
            # Maybe update? For now, just ignore or add new? 
            # Let's just insert new for now to avoid complex parsing of quantity strings.
             cursor.execute("INSERT INTO shopping_list (user_id, item_name, quantity, unit) VALUES (?, ?, ?, ?)", 
                           (user_id, item_name, quantity, unit))
        else:
            cursor.execute("INSERT INTO shopping_list (user_id, item_name, quantity, unit) VALUES (?, ?, ?, ?)", 
                           (user_id, item_name, quantity, unit))
        conn.commit()
        conn.close()

    def get_shopping_list(self, user_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_name, quantity, is_checked, unit FROM shopping_list WHERE user_id = ?", (user_id,))
        items = cursor.fetchall()
        conn.close()
        return items

    def update_shopping_item_status(self, user_id, item_id, is_checked):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE shopping_list SET is_checked = ? WHERE id = ? AND user_id = ?", (1 if is_checked else 0, item_id, user_id))
        conn.commit()
        conn.close()

    def delete_shopping_item(self, user_id, item_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list WHERE id = ? AND user_id = ?", (item_id, user_id))
        conn.commit()
        conn.close()

    def delete_checked_shopping_items(self, user_id):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list WHERE user_id = ? AND is_checked = 1", (user_id,))
        conn.commit()
        conn.close()
        
    def clear_shopping_list(self, user_id):
        # Clear all or only checked? Usually all or checked. 
        # Let's add method to clear checked items.
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shopping_list WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def update_shopping_item(self, user_id, item_id, name=None, quantity=None, unit=None):
        user_id = user_id or 0
        conn = self.get_connection()
        cursor = conn.cursor()
        if name is not None:
            cursor.execute("UPDATE shopping_list SET item_name = ? WHERE id = ? AND user_id = ?", (name, item_id, user_id))
        if quantity is not None:
            cursor.execute("UPDATE shopping_list SET quantity = ? WHERE id = ? AND user_id = ?", (quantity, item_id, user_id))
        if unit is not None:
            cursor.execute("UPDATE shopping_list SET unit = ? WHERE id = ? AND user_id = ?", (unit, item_id, user_id))
        conn.commit()
        conn.close()
