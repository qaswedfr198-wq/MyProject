import google.generativeai as genai
import os
import json
from PIL import Image

def get_ai_recommendation(family_data, inventory_data):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        import database
        api_key = database.get_setting("gemini_api_key")
        
    if not api_key:
        return "Error: GEMINI_API_KEY not set in Environment or Settings."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are a professional Nutritionist and Home Manager AI.
    
    Current Family Profile:
    {family_data}
    
    Current Inventory:
    {inventory_data}
    
    Based on the family's health conditions (Genetic diseases, Allergens) and the current inventory:
    1. Suggest a shopping list of essential healthy items missing.
    2. Suggest 1-2 simple recipes using current inventory (Avoid allergens!).
    3. Warn about any expired or near-expiry items.
    
    Keep the response concise and formatted as a checklist.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

def get_ai_chat_response(message, family_data, inventory_data):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        import database
        api_key = database.get_setting("gemini_api_key")
        
    if not api_key:
        return "Error: GEMINI_API_KEY not set. Please set it in Settings."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are a helpful Home Assistant specializing in Inventory and Nutrition management.
    
    Current Family Context:
    {family_data}
    
    Current Inventory Context:
    {inventory_data}
    
    User Question: {message}
    
    Answer the user's question based on the context above.
    - If asking about ingredients, check the inventory.
    - If suggesting recipes, consider allergens and available items.
    - Response should be friendly and concise (in the same language as the user's question).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

def recognize_food_from_image(image_path):
    """
    Recognize food items from an image and return structured data for inventory.
    Returns: dict with 'name', 'quantity', 'expiry_days', 'area'
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        import database
        api_key = database.get_setting("gemini_api_key")
        
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    # Flash is faster and good for vision tasks
    model = genai.GenerativeModel('gemini-1.5-flash')

    try:
        img = Image.open(image_path)
        prompt = """
        Analyze this image of food or groceries. 
        Identify the main item and provide:
        1. Item Name (English and Traditional Chinese)
        2. Suggested Quantity (integer)
        3. Estimated Expiry Days (integer from today, e.g., 7 for a week)
        4. Suggested Storage Area (e.g., Refrigerator, Pantry, Freezer)

        Return ONLY a JSON object in this format:
        {
            "name": "Chinese Name",
            "name_en": "English Name",
            "quantity": 1,
            "expiry_days": 7,
            "area": "Refrigerator"
        }
        """
        response = model.generate_content([prompt, img])
        
        # Clean response text as some models might wrap in ```json ... ```
        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:].strip()
        
        return json.loads(clean_text)
    except Exception as e:
        print(f"Vision AI Error: {e}")
        return None
