import pg8000.dbapi
import urllib.parse
import os
import time

CONNECTION_STRING = "postgresql://root:c8s1T9DIn04yFxt2NB5XvA7wE3WL6MRi@tpe1.clusters.zeabur.com:20243/zeabur"

def retry_db_operation(func):
    def wrapper(*args, **kwargs):
        attempts = 3
        while attempts > 0:
            try:
                return func(*args, **kwargs)
            except (pg8000.dbapi.DatabaseError, pg8000.dbapi.InterfaceError) as e:
                attempts -= 1
                if attempts == 0:
                    raise e
                print(f"DB Retry {func.__name__}: {e}")
                time.sleep(1)
            except Exception as e: # Catch generic exceptions just in case
                attempts -= 1
                if attempts == 0:
                    raise e
                print(f"DB Retry {func.__name__} (Generic): {e}")
                time.sleep(1)

    return wrapper

class RemoteBackend:
    def get_connection(self):
        try:
            result = urllib.parse.urlparse(CONNECTION_STRING)
            username = result.username
            password = result.password
            database = result.path[1:]
            hostname = result.hostname
            port = result.port
            
            return pg8000.dbapi.connect(
                user=username,
                password=password,
                host=hostname,
                port=port,
                database=database
            )
        except Exception as e:
            print(f"Connection failed: {e}, retrying...")
            time.sleep(1)
            # Retry logic duplicated for simplicity, ideally recursive or loopy
            result = urllib.parse.urlparse(CONNECTION_STRING)
            return pg8000.dbapi.connect(
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port,
                database=result.path[1:]
            )

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
                unit TEXT, -- Added unit column
                expiry_date TEXT,
                buy_date TEXT,
                area TEXT NOT NULL
            )
        ''')

        # Migration: Add unit column if not exists (for existing users)
        try:
            cursor.execute("ALTER TABLE app_inventory ADD COLUMN IF NOT EXISTS unit TEXT")
            conn.commit()
        except Exception as e:
            print(f"Migration Error (Inventory Unit): {e}")
            conn.rollback()
        
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

        # Chat History Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_chat_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Daily Recipes Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_daily_recipes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                date DATE NOT NULL,
                content TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        ''')

        # Kitchen Equipment Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_kitchen_equipment (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                equipment_name TEXT NOT NULL,
                UNIQUE(user_id, equipment_name)
            )
        ''')

        # Calorie Records Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_calories (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                date DATE NOT NULL,
                meal_type TEXT NOT NULL,
                food_name TEXT NOT NULL,
                calories INTEGER NOT NULL,
                note TEXT
            )
        ''')

        # Shopping List Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_shopping_list (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES app_users(id),
                item_name TEXT NOT NULL,
                quantity TEXT, 
                is_checked INTEGER DEFAULT 0,
                unit TEXT
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
    def add_inventory_item(self, user_id, name, quantity, unit, expiry_date, buy_date, area):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, quantity, expiry_date, buy_date FROM app_inventory WHERE user_id = %s AND name = %s AND area = %s AND unit IS NOT DISTINCT FROM %s", (user_id, name, area, unit))
        existing = cursor.fetchone()
        
        if existing:
            item_id, old_qty, old_expiry_date, old_buy_date = existing
            new_qty = old_qty + quantity
            # If dates are None, use new ones, else min/max logic or just new? Let's use logic from before
            final_expiry_date = expiry_date if not old_expiry_date else min(old_expiry_date, expiry_date)
            final_buy_date = buy_date if not old_buy_date else min(old_buy_date, buy_date)
            
            cursor.execute('''
                UPDATE app_inventory 
                SET quantity = %s, expiry_date = %s, buy_date = %s
                WHERE id = %s
            ''', (new_qty, final_expiry_date, final_buy_date, item_id))
        else:
            cursor.execute('''
                INSERT INTO app_inventory (user_id, name, quantity, unit, expiry_date, buy_date, area)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, name, quantity, unit, expiry_date, buy_date, area))
            
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
        cursor.execute("SELECT id, name, quantity, unit, expiry_date, buy_date, area FROM app_inventory WHERE user_id = %s AND area = %s ORDER BY expiry_date ASC", (user_id, area))
        items = cursor.fetchall()
        conn.close()
        return items

    @retry_db_operation
    def get_all_inventory(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, quantity, unit, expiry_date, buy_date, area FROM app_inventory WHERE user_id = %s", (user_id,))
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

    @retry_db_operation
    def update_inventory_item(self, user_id, item_id, name=None, quantity=None, unit=None, expiry_date=None, buy_date=None, area=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if quantity is not None:
            updates.append("quantity = %s")
            params.append(quantity)
        if unit is not None:
            updates.append("unit = %s")
            params.append(unit)
        if expiry_date is not None:
            updates.append("expiry_date = %s")
            params.append(expiry_date)
        if buy_date is not None:
            updates.append("buy_date = %s")
            params.append(buy_date)
        if area is not None:
            updates.append("area = %s")
            params.append(area)
            
        if not updates:
            conn.close()
            return
            
        sql = f"UPDATE app_inventory SET {', '.join(updates)} WHERE id = %s AND user_id = %s"
        params.extend([item_id, user_id])
        
        cursor.execute(sql, params)
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

    # --- Chat History Operations ---
    @retry_db_operation
    def add_chat_message(self, user_id, sender, message):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO app_chat_history (user_id, sender, message) VALUES (%s, %s, %s)", (user_id, sender, message))
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_chat_history(self, user_id, date_str=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if date_str:
            cursor.execute("SELECT sender, message, timestamp FROM app_chat_history WHERE user_id = %s AND timestamp::date = %s ORDER BY timestamp ASC", (user_id, date_str))
        else:
            cursor.execute("SELECT sender, message, timestamp FROM app_chat_history WHERE user_id = %s ORDER BY timestamp ASC", (user_id,))
        history = cursor.fetchall()
        conn.close()
        return history

    @retry_db_operation
    def clear_chat_history(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_chat_history WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_chat_dates(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT timestamp::date FROM app_chat_history WHERE user_id = %s ORDER BY timestamp::date DESC", (user_id,))
        dates = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        return dates

    # --- Daily Recipe Operations ---
    @retry_db_operation
    def save_daily_recipes(self, user_id, date_str, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_daily_recipes (user_id, date, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, date) DO UPDATE SET content = EXCLUDED.content
        ''', (user_id, date_str, content))
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_daily_recipes(self, user_id, date_str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM app_daily_recipes WHERE user_id = %s AND date = %s", (user_id, date_str))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None

    # --- Kitchen Equipment Operations ---
    @retry_db_operation
    def get_kitchen_equipment(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT equipment_name FROM app_kitchen_equipment WHERE user_id = %s", (user_id,))
        equipment = [row[0] for row in cursor.fetchall()]
        conn.close()
        return equipment

    @retry_db_operation
    def update_kitchen_equipment(self, user_id, equipment_list):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_kitchen_equipment WHERE user_id = %s", (user_id,))
        for name in equipment_list:
            cursor.execute("INSERT INTO app_kitchen_equipment (user_id, equipment_name) VALUES (%s, %s)", (user_id, name))
        conn.commit()
        conn.close()

    # --- Calorie Operations ---
    @retry_db_operation
    def add_calorie_record(self, user_id, date_str, meal_type, food_name, calories, note):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_calories (user_id, date, meal_type, food_name, calories, note)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        ''', (user_id, date_str, meal_type, food_name, calories, note))
        record_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return record_id

    @retry_db_operation
    def get_calorie_records(self, user_id, date_str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, meal_type, food_name, calories, note FROM app_calories WHERE user_id = %s AND date = %s", (user_id, date_str))
        records = cursor.fetchall()
        conn.close()
        return records

    @retry_db_operation
    def delete_calorie_record(self, user_id, record_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_calories WHERE id = %s AND user_id = %s", (record_id, user_id))
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_daily_calorie_total(self, user_id, date_str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(calories) FROM app_calories WHERE user_id = %s AND date = %s", (user_id, date_str))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else 0

    @retry_db_operation
    def get_daily_calorie_breakdown(self, user_id, date_str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT meal_type, SUM(calories) FROM app_calories WHERE user_id = %s AND date = %s GROUP BY meal_type", (user_id, date_str))
        results = cursor.fetchall()
        conn.close()
        return results

    @retry_db_operation
    def get_weekly_calorie_summary(self, user_id, end_date_str):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Get past 7 days (inclusive of end_date)
        # Using pure SQL for date generation might be complex depending on DB version, 
        # so let's just query the range and fill gaps in python, OR just valid records.
        # Since we just want the summary for existing records:
        cursor.execute('''
            SELECT date, SUM(calories) 
            FROM app_calories 
            WHERE user_id = %s AND date <= %s AND date > (%s::date - INTERVAL '7 days') 
            GROUP BY date
        ''', (user_id, end_date_str, end_date_str))
        
        results = cursor.fetchall()
        conn.close()
        return results

    # --- Shopping List Operations ---
    @retry_db_operation
    def add_shopping_item(self, user_id, item_name, quantity, unit=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if exists unchecked
        cursor.execute("SELECT id FROM app_shopping_list WHERE user_id = %s AND item_name = %s AND is_checked = 0", (user_id, item_name))
        existing = cursor.fetchone()
        
        if existing:
             # Insert new for simplicity as before
             cursor.execute("INSERT INTO app_shopping_list (user_id, item_name, quantity, unit) VALUES (%s, %s, %s, %s)", 
                           (user_id, item_name, quantity, unit))
        else:
            cursor.execute("INSERT INTO app_shopping_list (user_id, item_name, quantity, unit) VALUES (%s, %s, %s, %s)", 
                           (user_id, item_name, quantity, unit))
        conn.commit()
        conn.close()

    @retry_db_operation
    def get_shopping_list(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_name, quantity, is_checked, unit FROM app_shopping_list WHERE user_id = %s ORDER BY id DESC", (user_id,))
        items = cursor.fetchall()
        conn.close()
        return items

    @retry_db_operation
    def update_shopping_item_status(self, user_id, item_id, is_checked):
        conn = self.get_connection()
        cursor = conn.cursor()
        val = 1 if is_checked else 0
        cursor.execute("UPDATE app_shopping_list SET is_checked = %s WHERE id = %s AND user_id = %s", (val, item_id, user_id))
        conn.commit()
        conn.close()

    @retry_db_operation
    def delete_shopping_item(self, user_id, item_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_shopping_list WHERE id = %s AND user_id = %s", (item_id, user_id))
        conn.commit()
        conn.close()

    @retry_db_operation
    def delete_checked_shopping_items(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_shopping_list WHERE user_id = %s AND is_checked = 1", (user_id,))
        conn.commit()
        conn.close()
        
    @retry_db_operation
    def clear_shopping_list(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_shopping_list WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

    @retry_db_operation
    def update_shopping_item(self, user_id, item_id, name=None, quantity=None, unit=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if name is not None:
            cursor.execute("UPDATE app_shopping_list SET item_name = %s WHERE id = %s AND user_id = %s", (name, item_id, user_id))
        if quantity is not None:
            cursor.execute("UPDATE app_shopping_list SET quantity = %s WHERE id = %s AND user_id = %s", (quantity, item_id, user_id))
        if unit is not None:
            cursor.execute("UPDATE app_shopping_list SET unit = %s WHERE id = %s AND user_id = %s", (unit, item_id, user_id))
        conn.commit()
        conn.close()

