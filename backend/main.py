from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import google.generativeai as genai
import os
import json
import io
from PIL import Image
from dotenv import load_dotenv

# 讀取環境變數
load_dotenv()

app = FastAPI(title="Home Assistant AI Backend")

# 加入 CORS 支援
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def configure_genai():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return api_key
    return None

# 定義資料格式
class ChatRequest(BaseModel):
    message: str
    family_data: Optional[str] = ""
    inventory_data: Optional[str] = ""

class RecommendRequest(BaseModel):
    family_data: str
    inventory_data: str

@app.get("/")
async def root():
    return {"message": "Home Assistant AI Backend is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    api_key = configure_genai()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY IS MISSING IN ENVIRONMENT.")
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")
    
    print(f"[INFO] New chat request (Gemini 2.5 Flash): {request.message[:30]}...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are a helpful Home Assistant specializing in Inventory and Nutrition management.
    
    Current Family Context:
    {request.family_data}
    
    Current Inventory Context:
    {request.inventory_data}
    
    User Question: {request.message}
    
    Answer the user's question based on the context above.
    - If asking about ingredients, check the inventory.
    - If suggesting recipes, consider allergens and available items.
    - Response should be friendly and concise (in the same language as the user's question).
    """
    
    try:
        response = await model.generate_content_async(prompt)
        print("[INFO] AI Chat response successful.")
        return {"response": response.text}
    except Exception as e:
        print(f"[ERROR] AI Chat Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/recommend")
async def recommend(request: RecommendRequest):
    api_key = configure_genai()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY IS MISSING IN ENVIRONMENT.")
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")
    
    print("[INFO] New recommendation request (Gemini 2.5 Flash).")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are a professional Nutritionist and Home Manager AI.
    
    Current Family Profile:
    {request.family_data}
    
    Current Inventory:
    {request.inventory_data}
    
    Based on the family's health conditions (Genetic diseases, Allergens) and the current inventory:
    1. Suggest a shopping list of essential healthy items missing.
    2. Suggest 1-2 simple recipes using current inventory (Avoid allergens!).
    3. Warn about any expired or near-expiry items.
    
    Keep the response concise and formatted as a checklist.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        print("[INFO] AI Recommendation successful.")
        return {"recommendation": response.text}
    except Exception as e:
        print(f"[ERROR] AI Recommend Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/vision")
async def vision_recognition(file: UploadFile = File(...)):
    api_key = configure_genai()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY IS MISSING IN ENVIRONMENT.")
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")
    
    print(f"[INFO] New vision request (Gemini 2.5 Flash): {file.filename}")
    try:
        image_data = await file.read()
        img = Image.open(io.BytesIO(image_data))
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Analyze this image of food or groceries. 
        Identify the main item and provide:
        1. Item Name (English and Traditional Chinese)
        2. Suggested Quantity (integer)
        3. Estimated Expiry Days (integer from today, e.g., 7 for a week)
        4. Suggested Storage Area (e.g., Refrigerator, Pantry, Freezer)

        Return ONLY a JSON object in this format:
        {
            "name": "中文名稱",
            "name_en": "English Name",
            "quantity": 1,
            "expiry_days": 7,
            "area": "Refrigerator"
        }
        """
        
        response = await model.generate_content_async([prompt, img])
        
        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:].strip()
        
        print(f"[INFO] Vision AI response: {clean_text[:50]}...")
        return json.loads(clean_text)
    except Exception as e:
        print(f"[ERROR] Vision AI Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vision AI Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
