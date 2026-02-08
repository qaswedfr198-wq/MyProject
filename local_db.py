import sqlite3
import os

DB_NAME = "inventory.db"

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
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                expiry_date TEXT,
                buy_date TEXT,
                area TEXT NOT NULL
            )
        ''')
        
        # Family Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                allergens TEXT,
                genetic TEXT,
                height REAL,
                weight REAL
            )
        ''')
        
        # Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Quick Replies Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        ''')
        
        # Migrations
        try:
            cursor.execute("ALTER TABLE family ADD COLUMN height REAL")
        except sqlite3.OperationalError:
            pass 
        try:
            cursor.execute("ALTER TABLE family ADD COLUMN weight REAL")
        except sqlite3.OperationalError:
            pass 
        
        conn.commit()
        conn.close()

    # --- Inventory Operations ---
    def add_inventory_item(self, user_id, name, quantity, expiry_date, buy_date, area):
        # user_id is ignored for local db as it's single user
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, quantity, expiry_date, buy_date FROM inventory WHERE name = ? AND area = ?", (name, area))
        existing = cursor.fetchone()
        
        if existing:
            item_id, old_qty, old_expiry_date, old_buy_date = existing
            new_qty = old_qty + quantity
            final_expiry_date = min(old_expiry_date, expiry_date)
            final_buy_date = min(old_buy_date, buy_date)
            
            cursor.execute('''
                UPDATE inventory 
                SET quantity = ?, expiry_date = ?, buy_date = ?
                WHERE id = ?
            ''', (new_qty, final_expiry_date, final_buy_date, item_id))
        else:
            cursor.execute('''
                INSERT INTO inventory (name, quantity, expiry_date, buy_date, area)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, quantity, expiry_date, buy_date, area))
            
        conn.commit()
        conn.close()

    def update_item_quantity(self, user_id, item_id, delta):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantity FROM inventory WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            current_qty = row[0]
            new_qty = current_qty + delta
            
            if new_qty <= 0:
                cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            else:
                cursor.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))
                
        conn.commit()
        conn.close()

    def get_items_by_area(self, user_id, area):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE area = ? ORDER BY date ASC", (area,))
        items = cursor.fetchall()
        conn.close()
        return items

    def get_all_inventory(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory")
        items = cursor.fetchall()
        conn.close()
        return items

    def delete_inventory_item(self, user_id, item_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    # --- Family Operations ---
    def add_family_member(self, user_id, name, age, gender, allergens, genetic, height, weight):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO family (name, age, gender, allergens, genetic, height, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, age, gender, allergens, genetic, height, weight))
        conn.commit()
        conn.close()

    def get_family_members(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM family")
        members = cursor.fetchall()
        conn.close()
        return members

    def update_family_member(self, user_id, member_id, name, age, gender, allergens, genetic, height, weight):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE family 
            SET name=?, age=?, gender=?, allergens=?, genetic=?, height=?, weight=?
            WHERE id=?
        ''', (name, age, gender, allergens, genetic, height, weight, member_id))
        conn.commit()
        conn.close()

    def delete_family_member(self, user_id, member_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM family WHERE id = ?", (member_id,))
        conn.commit()
        conn.close()

    # --- Settings Operations ---
    def get_setting(self, user_id, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def set_setting(self, user_id, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    # --- Quick Replies Operations ---
    def add_quick_reply(self, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quick_replies (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()

    def get_quick_replies(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quick_replies")
        replies = cursor.fetchall()
        conn.close()
        return replies

    def delete_quick_reply(self, reply_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quick_replies WHERE id = ?", (reply_id,))
        conn.commit()
        conn.close()
