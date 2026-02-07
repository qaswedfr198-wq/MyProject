import sqlite3
import os

DB_NAME = "inventory.db"

def migrate_database():
    """
    遷移資料庫：將舊欄位名稱 (foodname, date, buydate) 
    改為新欄位名稱 (name, expiry_date, buy_date)
    """
    print("開始資料庫遷移...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 檢查是否存在舊的 inventory 表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("inventory 表不存在，無需遷移。")
        conn.close()
        return
    
    # 檢查是否已經是新結構（檢查是否有 name 欄位）
    cursor.execute("PRAGMA table_info(inventory)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'name' in column_names:
        print("資料庫已經是新結構，無需遷移。")
        conn.close()
        return
    
    if 'foodname' not in column_names:
        print("警告：資料庫結構異常，無法識別。")
        conn.close()
        return
    
    print("檢測到舊結構，開始遷移...")
    
    # 1. 備份現有資料到臨時表
    print("步驟 1/5: 備份現有資料...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_backup AS 
        SELECT * FROM inventory
    """)
    
    # 計算備份的資料筆數
    cursor.execute("SELECT COUNT(*) FROM inventory_backup")
    backup_count = cursor.fetchone()[0]
    print(f"  已備份 {backup_count} 筆資料")
    
    # 2. 刪除舊表
    print("步驟 2/5: 刪除舊表...")
    cursor.execute("DROP TABLE inventory")
    
    # 3. 創建新表（使用新欄位名稱）
    print("步驟 3/5: 創建新表結構...")
    cursor.execute('''
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date TEXT,
            buy_date TEXT,
            area TEXT NOT NULL
        )
    ''')
    
    # 4. 將資料從備份表遷移到新表
    print("步驟 4/5: 遷移資料...")
    cursor.execute("""
        INSERT INTO inventory (id, name, quantity, expiry_date, buy_date, area)
        SELECT id, foodname, quantity, date, buydate, area
        FROM inventory_backup
    """)
    
    # 計算遷移的資料筆數
    cursor.execute("SELECT COUNT(*) FROM inventory")
    migrated_count = cursor.fetchone()[0]
    print(f"  已遷移 {migrated_count} 筆資料")
    
    # 5. 刪除備份表
    print("步驟 5/5: 清理備份表...")
    cursor.execute("DROP TABLE inventory_backup")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 資料庫遷移完成！")
    print(f"   總共遷移了 {migrated_count} 筆庫存資料")
    print(f"   新欄位名稱：id, name, quantity, expiry_date, buy_date, area")

if __name__ == "__main__":
    # 檢查資料庫檔案是否存在
    if not os.path.exists(DB_NAME):
        print(f"資料庫檔案 {DB_NAME} 不存在。")
        print("將在首次運行應用程式時自動創建新結構。")
    else:
        migrate_database()
