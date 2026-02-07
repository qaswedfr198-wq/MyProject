# Kivy Inventory & Family Health App

## Overview
A Python mobile application built with KivyMD to manage home inventory and track family health profiles. Connects to Google Gemini API for smart shopping recommendations.

## Features
- **Family Dashboard**: Track members' stats (Age, BMI, Conditions) in a modern dashboard style.
- **Inventory Management**: Track food items across 4 zones (Frozen, Fridge, Dry,Seasoning). *[Coming in next update]*
- **AI Chat**: Get shopping lists and recipes based on your family's health needs and current stock.

## Installation

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you have trouble collecting requirements, try:*
   ```bash
   pip install kivy kivymd google-generativeai
   ```

## Configuration

Set your Google Gemini API Key:
- **Windows (PowerShell)**: `$env:GEMINI_API_KEY="YOUR_KEY_HERE"`
- **Linux/Mac**: `export GEMINI_API_KEY="YOUR_KEY_HERE"`

## Usage

Run the app:
```bash
python main.py
```

- **Home Screen**: Add family members using the `+` button.
- **Inventory/AI**: Tabs available for navigation (Placeholders for now).

## File Structure
- `main.py`: Entry point and UI logic.
- `database.py`: SQLite database manager.
- `ai_manager.py`: Google Gemini API wrapper.
- `assets/`: Image resources.
