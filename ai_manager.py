import requests
import json
import os
import threading
from kivy.clock import Clock

# 雲端後端網址 (不含最後的斜線)
BACKEND_URL = "https://ai-home-helper.zeabur.app"

def run_in_background(target, callback, *args, **kwargs):
    """
    Helper function to run a target function in a background thread
    and schedule the callback on the main thread with the result.
    """
    def thread_func():
        try:
            print(f"[AI Manager] Starting background task: {target.__name__}")
            result = target(*args, **kwargs)
            # Schedule the callback on the main thread
            Clock.schedule_once(lambda dt: callback(result), 0)
            print(f"[AI Manager] Task completed: {target.__name__}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[AI Manager] Error in background task: {e}")
            # Schedule callback with None/Error if possible? Or just notify UI directly?
            # It's better to let callback handle None or modify signatures. 
            # For now, let's just callback(None) assuming that signals failure in most cases here.
            Clock.schedule_once(lambda dt: callback(None), 0)
    
    threading.Thread(target=thread_func).start()



def get_ai_chat_response(message, family_data, inventory_data, equipment_data=""):
    """
    從雲端後端取得 AI 聊天回覆 (Blocking)
    """
    url = f"{BACKEND_URL}/chat"
    # Append system instructions to the message to ensure structured data is returned for recipes/ingredients
    system_instruction = """
(系統指示：請盡量使用使用者的「庫存食材」來進行回答或推薦食譜。
若你的回答包含食譜或特定的食材清單，請在回覆最後附加一個隱藏的 [INGREDIENTS_JSON] 區塊。
格式必須為：
[INGREDIENTS_JSON]
[
  {"name": "食譜名稱", "ingredients": [{"name": "食材1", "qty": 100, "unit": "g"}, ...], "shopping_list": [...]},
  ...
]
請確保單位統一使用 g, ml, 個(unit)。若為多個食譜請分開列出。)
"""
    full_message = f"{message}\n\n{system_instruction}"
    
    payload = {
        "message": full_message,
        "family_data": str(family_data),
        "inventory_data": str(inventory_data),
        "equipment_data": str(equipment_data)
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "AI 目前沒有回應。")
    except Exception as e:
        return f"連線至 AI 伺服器失敗: {str(e)}"

def get_ai_chat_response_async(callback, message, family_data, inventory_data, equipment_data=""):
    """
    Async version of get_ai_chat_response
    """
    run_in_background(get_ai_chat_response, callback, message, family_data, inventory_data, equipment_data)

def recognize_food_from_image(image_path):
    """
    將圖片傳送到雲端後端進行食材辨識 (Blocking)
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

def recognize_food_from_image_async(callback, image_path):
    """
    Async version of recognize_food_from_image
    """
    run_in_background(recognize_food_from_image, callback, image_path)

def recognize_calories_from_image(image_path):
    """
    Chains vision recognition and calorie estimation (Blocking)
    """
    vision_result = recognize_food_from_image(image_path)
    if vision_result and "name" in vision_result:
        food_name = vision_result["name"]
        calories = estimate_calories(food_name)
        return {"name": food_name, "calories": calories}
    return None

def recognize_calories_from_image_async(callback, image_path):
    """
    Async version of recognize_calories_from_image
    """
    run_in_background(recognize_calories_from_image, callback, image_path)

def estimate_calories(food_name):
    """
    估算食物卡路里，回傳整數 (Blocking)
    """
    prompt = f"Estimate calories for '{food_name}'. Return ONLY the integer number (e.g. 300). Do not return any text."
    # Use empty context as we only need general knowledge
    response = get_ai_chat_response(prompt, "", "")
    
    # Try to parse integer from response
    try:
        import re
        # Find all number sequences
        digits = re.findall(r'\d+', response)
        if digits:
            # Return the first number found
            return int(digits[0])
        else:
            return None
    except:
        return None

def estimate_calories_async(callback, food_name):
    """
    Async version of estimate_calories
    """
    run_in_background(estimate_calories, callback, food_name)

def estimate_item_category(item_name):
    """
    Estimate the category for an item (Frozen, Fridge, Dry Goods, Seasoning, General).
    Returns one of: 冷凍, 冷藏, 乾貨, 調味料, 一般
    """
    prompt = f"""
    Categorize the food item '{item_name}' into one of these categories:
    1. 冷凍 (Frozen)
    2. 冷藏 (Fridge/Refrigerated)
    3. 乾貨 (Dry Goods/Pantry)
    4. 調味料 (Seasoning/Condiments)
    5. 一般 (General/Other)

    Return ONLY the category name in Chinese (冷凍, 冷藏, 乾貨, 調味料, 一般).
    If unsure, return '一般'.
    """
    response = get_ai_chat_response(prompt, "", "")
    
    # Simple matching
    for cat in ["冷凍", "冷藏", "乾貨", "調味料"]:
        if cat in response:
            return cat
    return "一般"

def estimate_item_category_async(callback, item_name):
    """
    Async version of estimate_item_category
    """
    run_in_background(estimate_item_category, callback, item_name)

def get_daily_recipe_recommendations_async(callback, family_data, equipment_data, inventory_data):
    run_in_background(get_daily_recipe_recommendations, callback, family_data, equipment_data, inventory_data)

def get_daily_recipe_recommendations(family_data, equipment_data, inventory_data):
    """
    Get 1 recipe recommendation based on family data, available equipment, and inventory.
    """
    family_info = ""
    if not family_data:
        family_info = "目前暫無家合成員詳細資料，請提供一般健康家庭的推薦。"
    else:
        for m in family_data:
            # Table Schema: id, name, gender, age, height, weight, allergens, genetic_conditions
            try:
                # members might be tuples from sqlite fetchall
                if isinstance(m, (tuple, list)) and len(m) >= 8:
                    _, name, gender, age, height, weight, allergens, gen = m[:8]
                    family_info += f"- {name}: {gender}, {age}歲, 身高{height}cm, 體重{weight}kg, 過敏原: {allergens}, 遺傳病: {gen}\n"
                elif isinstance(m, dict):
                    family_info += f"- {m.get('name')}: {m.get('gender')}, {m.get('age')}歲, 身高{m.get('height')}cm, 體重{m.get('weight')}kg, 過敏原: {m.get('allergens')}, 遺傳病: {m.get('genetic_conditions')}\n"
            except Exception as e:
                print(f"[AI Manager] Error parsing member: {e}")
    
    equipment_info = ", ".join(equipment_data) if equipment_data else "無特定設備（僅使用一般瓦斯爐與鍋具）"

    inventory_info = ""
    if inventory_data:
        # id, name, qty, unit, expiry, buy, area
        inv_list = []
        for item in inventory_data:
            try:
                # item[1] is name, item[2] is quantity, item[3] is unit
                i_name = item[1]
                i_qty = item[2]
                i_unit = item[3] if item[3] else "unit"
                inv_list.append(f"{i_name} ({i_qty} {i_unit})")
            except:
                pass
        inventory_info = ", ".join(inv_list)
    else:
        inventory_info = "目前冰箱空空如也"
    
    prompt = f"""
你是一位專業的營養師與大廚。根據以下家庭成員資料、可用的廚房設備以及「現有庫存食材」，請提供 1 道最適合他們的健康食譜。

【重要：絕對只能推薦 1 道食譜，禁止推薦 2 道或以上！】

成員資料：
{family_info}

可用廚房設備：
{equipment_info}

現有庫存食材（請優先使用這些食材）：
{inventory_info}

請注意：
1. 完全避開過敏原。
2. 僅使用目前現有的廚房設備進行烹飪。
3. **核心目標**：必須盡量「僅使用現有庫存食材」來設計食譜，目標是讓使用者不需要額外採買即可烹飪。
4. **食材應用**：若現有食材足以組成一道料理，則應優先以此為主軸，避免加入需要額外購買的主材料。

5. 輸出格式必須是純 JSON，結構如下（recipes 陣列中只能有一個物件）：
{{
  "recipes": [
    {{
      "name": "食譜名稱",
      "calories": 500,
      "intro": "這道菜的簡單介紹",
      "ingredients": [
          {{"name": "食材名稱1", "qty": 300, "unit": "g"}},
          {{"name": "食材名稱2", "qty": 1, "unit": "unit"}}
      ],
      "steps": ["步驟1", "步驟2"],
      "shopping_list": [
          {{"name": "食材名稱1", "qty": 300, "unit": "g"}},
          {{"name": "食材名稱2", "qty": 1, "unit": "unit"}}
      ],
      "image_keywords": "Calculated English keywords for image generation (e.g. delicious rainbow chicken breast with brown rice, photorealistic, 4k)"
    }}
  ]
}}
重要：ingredients 與 shopping_list 欄位中的 name 必須與庫存食材名稱一致，qty 為數字，unit 為單位 (g, ml, unit)。
只輸出 JSON，不要有額外文字。
"""
    try:
        response = get_ai_chat_response(prompt, family_data, inventory_data, equipment_data)
        # Cleanup JSON if there's markdown formatting
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        return json.loads(response)
    except Exception as e:
        print(f"[AI Manager] Error parsing recipes: {e}")
        return None

def get_restaurant_recommendation_async(callback, family_data):
    run_in_background(get_restaurant_recommendation, callback, family_data)

def get_restaurant_recommendation(family_data):
    """
    Get restaurant recommendation based on family data (health conditions).
    Returns JSON with recommendation text and search query.
    """
    family_info = ""
    if not family_data:
        family_info = "無特定健康限制，請推薦一般大眾喜愛的美食。"
    else:
        for m in family_data:
            try:
                if isinstance(m, (tuple, list)) and len(m) >= 8:
                    _, name, gender, age, height, weight, allergens, gen = m[:8]
                    family_info += f"- {name}: {gender}, {age}歲, 過敏原: {allergens}, 遺傳病: {gen}\n"
                elif isinstance(m, dict):
                    family_info += f"- {m.get('name')}: 過敏原: {m.get('allergens')}, 遺傳病: {m.get('genetic_conditions')}\n"
            except:
                pass

    prompt = f"""
你是一位專業的營養師與美食家。使用者現在在外面想找餐廳吃飯。
根據以下家庭成員資料，請推薦一種適合他們的「餐廳類型」或「料理風格」，並給出要在 Google Maps 搜尋的關鍵字。

成員資料：
{family_info}

請注意：
1. 必須完全避開成員的過敏原。
2. 若成員有慢性病（如高血壓、糖尿病），請推薦較為健康的類型（例如：清蒸、少油鹽）。
3. 不需要管家裡的廚房設備。
4. 輸出僅限 JSON 格式，不要有額外文字：
{{
  "recommendation": "針對你們的狀況，建議尋找...（簡短建議，100字內）",
  "search_query": "Google Maps 搜尋關鍵字 (例如：附近 清淡養生料理)"
}}
"""
    try:
        response = get_ai_chat_response(prompt, family_data, [])
        # Cleanup JSON
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        return json.loads(response)
        return json.loads(response)
    except Exception as e:
        print(f"[AI Manager] Error parsing restaurant recommendation: {e}")
        return None

def download_recipe_image_async(callback, keywords):
    run_in_background(download_recipe_image, callback, keywords)

def download_recipe_image(keywords):
    """
    Downloads the image from Pollinations.ai based on keywords and saves it locally.
    Returns the local file path or None if failed.
    """
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(keywords)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"
        
        # Create cache dir if not exists
        cache_dir = os.path.join(os.getcwd(), "cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Use a fixed name or timestamp? Fixed name allows overwriting old temp images to save space
        # But we might have multiple recipes in history?
        # For "Today's", we can just use `todays_recipe.jpg`
        import time
        filename = f"recipe_{int(time.time())}.jpg"
        save_path = os.path.join(cache_dir, filename)
        
        print(f"[AI Manager] Downloading image from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
            
        print(f"[AI Manager] Image saved to {save_path}")
        return save_path
    except Exception as e:
        print(f"[AI Manager] Image download failed: {e}")
        return None
