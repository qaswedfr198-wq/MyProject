from local_db import LocalBackend
from remote_db import RemoteBackend

# Global State
current_backend = None
current_user_id = None

def get_backend():
    global current_backend
    if current_backend is None:
        # Before login, we default to LocalBackend BUT this should only be used 
        # for checking local settings (remember me). 
        # User must login (setting current_backend to RemoteBackend) to access data.
        current_backend = LocalBackend()
    return current_backend

def init_db():
    # Initialize both just in case, or just the default one.
    # For now, we initialize the current one (Local).
    # When switching to Remote, we might need to call init_db on it too.
    get_backend().init_db()

# --- Auth / State Management ---
def login(username, password):
    global current_backend, current_user_id
    temp_backend = RemoteBackend()
    try:
        user_id = temp_backend.login_user(username, password)
        if user_id:
            current_backend = temp_backend
            current_user_id = user_id
            current_backend.init_db() # Ensure tables exist
            return True
        return False
    except Exception as e:
        print(f"Login error: {e}")
        return False

def register(username, password):
    global current_backend, current_user_id
    temp_backend = RemoteBackend()
    try:
        # Ensure tables exist before registering
        temp_backend.init_db() 
        user_id = temp_backend.register_user(username, password)
        if user_id:
            current_backend = temp_backend
            current_user_id = user_id
            return True
        return False
    except Exception as e:
        print(f"Register error: {e}")
        return False

def logout():
    global current_backend, current_user_id
    current_backend = LocalBackend()
    current_user_id = None

def is_local():
    return isinstance(get_backend(), LocalBackend)

# --- Inventory Operations ---
def add_inventory_item(name, quantity, unit, expiry_date, buy_date, area):
    get_backend().add_inventory_item(current_user_id, name, quantity, unit, expiry_date, buy_date, area)

def update_item_quantity(item_id, delta):
    get_backend().update_item_quantity(current_user_id, item_id, delta)

def get_items_by_area(area):
    return get_backend().get_items_by_area(current_user_id, area)

def get_all_inventory():
    return get_backend().get_all_inventory(current_user_id)

def delete_inventory_item(item_id):
    get_backend().delete_inventory_item(current_user_id, item_id)

def update_inventory_item(item_id, name=None, quantity=None, unit=None, expiry_date=None, buy_date=None, area=None):
    get_backend().update_inventory_item(current_user_id, item_id, name, quantity, unit, expiry_date, buy_date, area)

# --- Family Operations ---
def add_family_member(name, age, gender, allergens, genetic, height, weight):
    get_backend().add_family_member(current_user_id, name, age, gender, allergens, genetic, height, weight)

def get_family_members():
    return get_backend().get_family_members(current_user_id)

def update_family_member(member_id, name, age, gender, allergens, genetic, height, weight):
    get_backend().update_family_member(current_user_id, member_id, name, age, gender, allergens, genetic, height, weight)

def delete_family_member(member_id):
    get_backend().delete_family_member(current_user_id, member_id)

# --- Settings Operations ---
def get_setting(key):
    return get_backend().get_setting(current_user_id, key)

def set_setting(key, value):
    get_backend().set_setting(current_user_id, key, value)

def get_local_setting(key):
    # Always access local DB for device-specific settings like "Remember Me"
    return LocalBackend().get_setting(None, key)

def save_local_setting(key, value):
    # Always save to local DB
    LocalBackend().set_setting(None, key, value)

# --- Quick Replies Operations ---
def add_quick_reply(content):
    # Only support local quick replies for now
    LocalBackend().add_quick_reply(current_user_id, content)

def get_quick_replies():
    return LocalBackend().get_quick_replies(current_user_id)

def delete_quick_reply(reply_id):
    LocalBackend().delete_quick_reply(current_user_id, reply_id)

# --- Chat History Operations ---
def add_chat_message(sender, message):
    get_backend().add_chat_message(current_user_id, sender, message)

def get_chat_history(date_str=None):
    return get_backend().get_chat_history(current_user_id, date_str)

def get_chat_dates():
    return get_backend().get_chat_dates(current_user_id)

def save_daily_recipes(date_str, content):
    get_backend().save_daily_recipes(current_user_id, date_str, content)

def get_daily_recipes(date_str):
    return get_backend().get_daily_recipes(current_user_id, date_str)

def get_kitchen_equipment():
    return get_backend().get_kitchen_equipment(current_user_id)

def update_kitchen_equipment(equipment_list):
    get_backend().update_kitchen_equipment(current_user_id, equipment_list)

def clear_chat_history():
    get_backend().clear_chat_history(current_user_id)

# --- Calorie Operations ---
def add_calorie_record(date, meal_type, food_name, calories, note=""):
    return get_backend().add_calorie_record(current_user_id, date, meal_type, food_name, calories, note)

def get_calorie_records(date):
    return get_backend().get_calorie_records(current_user_id, date)

def delete_calorie_record(record_id):
    get_backend().delete_calorie_record(current_user_id, record_id)

def get_daily_calorie_total(date):
    return get_backend().get_daily_calorie_total(current_user_id, date)

def get_daily_calorie_breakdown(date):
    return get_backend().get_daily_calorie_breakdown(current_user_id, date)

def get_weekly_calorie_summary(end_date):
    return get_backend().get_weekly_calorie_summary(current_user_id, end_date)

# --- Shopping List Operations ---
def add_shopping_item(item_name, quantity, unit=""):
    get_backend().add_shopping_item(current_user_id, item_name, quantity, unit)

def get_shopping_list():
    return get_backend().get_shopping_list(current_user_id)

def update_shopping_item_status(item_id, is_checked):
    get_backend().update_shopping_item_status(current_user_id, item_id, is_checked)

def delete_shopping_item(item_id):
    get_backend().delete_shopping_item(current_user_id, item_id)

def delete_checked_shopping_items():
    get_backend().delete_checked_shopping_items(current_user_id)

def clear_shopping_list():
    get_backend().clear_shopping_list(current_user_id)

def update_shopping_item(item_id, name=None, quantity=None, unit=None):
    get_backend().update_shopping_item(current_user_id, item_id, name, quantity, unit)
