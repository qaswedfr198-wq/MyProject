import database
import os

try:
    print("Initializing DB...")
    database.init_db()
    
    print("Testing save_local_setting...")
    database.save_local_setting("test_key", "test_value")
    
    print("Testing get_local_setting...")
    val = database.get_local_setting("test_key")
    print(f"Got value: {val}")
    
    assert val == "test_value"
    print("DB Test Passed!")
except Exception as e:
    print(f"DB Test Failed: {e}")
    import traceback
    traceback.print_exc()
