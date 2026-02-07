import requests
import json
import os

# 雲端後端網址 (不含最後的斜線)
BACKEND_URL = "https://ai-home-helper.zeabur.app"

def get_ai_recommendation(family_data, inventory_data):
    """
    從雲端後端取得營養與庫存建議
    """
    url = f"{BACKEND_URL}/recommend"
    payload = {
        "family_data": str(family_data),
        "inventory_data": str(inventory_data)
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("recommendation", "無法取得 AI 建議。")
    except Exception as e:
        return f"連線至 AI 伺服器失敗: {str(e)}"

def get_ai_chat_response(message, family_data, inventory_data):
    """
    從雲端後端取得 AI 聊天回覆
    """
    url = f"{BACKEND_URL}/chat"
    payload = {
        "message": message,
        "family_data": str(family_data),
        "inventory_data": str(inventory_data)
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "AI 目前沒有回應。")
    except Exception as e:
        return f"連線至 AI 伺服器失敗: {str(e)}"

def recognize_food_from_image(image_path):
    """
    將圖片傳送到雲端後端進行食材辨識
    """
    url = f"{BACKEND_URL}/vision"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=60)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Vision AI 連線錯誤: {e}")
        return None
