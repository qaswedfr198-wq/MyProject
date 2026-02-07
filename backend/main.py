from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 讀取環境變數
load_dotenv()

app = FastAPI(title="Home Assistant AI Backend")

# 加入 CORS 支援
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源，開發階段較方便
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.post("/recommend")
async def recommend(request: RecommendRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
        return {"recommendation": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
