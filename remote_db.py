import psycopg2
import os
import time

CONNECTION_STRING = "postgresql://root:c8s1T9DIn04yFxt2NB5XvA7wE3WL6MRi@tpe1.clusters.zeabur.com:20243/zeabur"

def retry_db_operation(func):
    def wrapper(*args, **kwargs):
        attempts = 3
        while attempts > 0:
            try:
                return func(*args, **kwargs)
            except psycopg2.OperationalError as e:
                attempts -= 1
                if attempts == 0:
                    raise e
                print(f"DB Retry {func.__name__}: {e}")
                time.sleep(1)
            except psycopg2.InterfaceError as e:
                attempts -= 1
                if attempts == 0:
                    raise e
                print(f"DB Retry {func.__name__}: {e}")
                time.sleep(1)
    return wrapper

class RemoteBackend:
    def get_connection(self):
        try:
            return psycopg2.connect(CONNECTION_STRING)
        except psycopg2.OperationalError as e:
            print(f"Connection failed: {e}, retrying...")
            time.sleep(1)
            return psycopg2.connect(CONNECTION_STRING)

    @retry_db_operation
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # User Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Inventory Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_inventory (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                expiry_date TEXT,
                buy_date TEXT,
                area TEXT NOT NULL
            )
        ''')
        
        # Family Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_family (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
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
            CREATE TABLE IF NOT EXISTS app_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                key TEXT NOT NULL,
                value TEXT,
                UNIQUE(user_id, key)
            )
        ''')
        
        conn.commit()
        conn.close()

    # --- Auth Operations ---
    @retry_db_operation
    def register_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO app_users (username, password) VALUES (%s, %s) RETURNING id", (username, password))
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id
        except psycopg2.IntegrityError:
            conn.rollback()
            return None
        finally:
            conn.close()

    @retry_db_operation
    def login_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM app_users WHERE username = %s AND password = %s", (username, password))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    # --- Inventory Operations ---
    @retry_db_operation
    def add_inventory_item(self, user_id, name, quantity, expiry_date, buy_date, area):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, quantity, expiry_date, buy_date FROM app_inventory WHERE user_id = %s AND name = %s AND area = %s", (user_id, name, area))
        existing = cursor.fetchone()
        
        if existing:
            item_id, old_qty, old_expiry_date, old_buy_date = existing
            new_qty = old_qty + quantity
            final_expiry_date = min(old_expiry_date, expiry_date)
            final_buy_date = min(old_buy_date, buy_date)
            
            cursor.execute('''
                UPDATE app_inventory 
                SET quantity = %s, expiry_date = %s, buy_date = %s
                WHERE id = %s
            ''', (new_qty, final_expiry_date, final_buy_date, item_id))
        else:
            cursor.execute('''
                INSERT INTO app_inventory (user_id, name, quantity, expiry_date, buy_date, area)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, name, quantity, expiry_date, buy_date, area))
            
        conn.commit()
        conn.close()

    @retry_db_operation
    def update_item_quantity(self, user_id, item_id, delta):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantity FROM app_inventory WHERE id = %s AND user_id = %s", (item_id, user_id))
        row = cursor.fetchone()
        if row:
            current_qty = row[0]
            new_qty = current_qty + delta
            
            if new_qty <= 0:
                cursor.execute("DELETE FROM app_inventory WHERE id = %s", (item_id,))
            else:
                cursor.execute("UPDATE app_inventory SET quantity = %s WHERE id = %s", (new_qty, item_id))
                
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_items_by_area(self, user_id, area):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, quantity, expiry_date, buy_date, area FROM app_inventory WHERE user_id = %s AND area = %s ORDER BY expiry_date ASC", (user_id, area))
        items = cursor.fetchall()
        conn.close()
        return items

    @retry_db_operation
    def get_all_inventory(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, quantity, expiry_date, buy_date, area FROM app_inventory WHERE user_id = %s", (user_id,))
        items = cursor.fetchall()
        conn.close()
        return items

    @retry_db_operation
    def delete_inventory_item(self, user_id, item_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_inventory WHERE id = %s AND user_id = %s", (item_id, user_id))
        conn.commit()
        conn.close()

    # --- Family Operations ---
    @retry_db_operation
    def add_family_member(self, user_id, name, age, gender, allergens, genetic, height, weight):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_family (user_id, name, age, gender, allergens, genetic, height, weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, name, age, gender, allergens, genetic, height, weight))
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_family_members(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age, gender, allergens, genetic, height, weight FROM app_family WHERE user_id = %s", (user_id,))
        members = cursor.fetchall()
        conn.close()
        return members

    @retry_db_operation
    def update_family_member(self, user_id, member_id, name, age, gender, allergens, genetic, height, weight):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE app_family 
            SET name=%s, age=%s, gender=%s, allergens=%s, genetic=%s, height=%s, weight=%s
            WHERE id=%s AND user_id=%s
        ''', (name, age, gender, allergens, genetic, height, weight, member_id, user_id))
        conn.commit()
        conn.close()

    @retry_db_operation
    def delete_family_member(self, user_id, member_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_family WHERE id = %s AND user_id = %s", (member_id, user_id))
        conn.commit()
        conn.close()

    # --- Settings Operations ---
    @retry_db_operation
    def get_setting(self, user_id, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE user_id = %s AND key = %s", (user_id, key))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    @retry_db_operation
    def set_setting(self, user_id, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_settings (user_id, key, value) 
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, key) 
            DO UPDATE SET value = EXCLUDED.value
        ''', (user_id, key, value))
        conn.commit()
        conn.close()
