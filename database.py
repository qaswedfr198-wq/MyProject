from local_db import LocalBackend
from remote_db import RemoteBackend

# Global State
current_backend = None
current_user_id = None

def get_backend():
    global current_backend
    if current_backend is None:
        # Default to LocalBackend if not set (e.g. before login, or guest mode)
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
def add_inventory_item(name, quantity, expiry_date, buy_date, area):
    get_backend().add_inventory_item(current_user_id, name, quantity, expiry_date, buy_date, area)

def update_item_quantity(item_id, delta):
    get_backend().update_item_quantity(current_user_id, item_id, delta)

def get_items_by_area(area):
    return get_backend().get_items_by_area(current_user_id, area)

def get_all_inventory():
    return get_backend().get_all_inventory(current_user_id)

def delete_inventory_item(item_id):
    get_backend().delete_inventory_item(current_user_id, item_id)

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
    LocalBackend().add_quick_reply(content)

def get_quick_replies():
    return LocalBackend().get_quick_replies()

def delete_quick_reply(reply_id):
    LocalBackend().delete_quick_reply(reply_id)
