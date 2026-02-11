from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.spinner import MDSpinner
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock
import os
import json
from datetime import datetime
import database
import ai_manager
from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_TEXT_DARK_GREY

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'TATA'))

class RecipeCard(MDCard):
    def __init__(self, recipe_data, click_callback, **kwargs):
        super().__init__(**kwargs)
        self.recipe_data = recipe_data
        self.click_callback = click_callback
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(280) # Taller card
        self.padding = 0
        self.radius = [dp(15)]
        self.elevation = 2
        self.ripple_behavior = True # Clickable look
        self.on_release = lambda: self.click_callback(self.recipe_data)
        
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        self.md_bg_color = [0.15, 0.15, 0.15, 1] if is_dark else [1, 1, 1, 1]
        
        # Image Logic
        local_img = recipe_data.get("local_image_path")
        img_keywords = recipe_data.get("image_keywords")
        img_box = FloatLayout(size_hint_y=0.75) # Increased image area
        
        if local_img and os.path.exists(local_img):
            # Use preloaded local image
            from kivy.uix.image import Image
            img_box.add_widget(Image(
                source=local_img,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=False
            ))
        elif img_keywords:
            # Fallback to Async if for some reason local failed but keywords exist (though our logic avoids this)
            from kivy.uix.image import AsyncImage
            import urllib.parse
            encoded_prompt = urllib.parse.quote(img_keywords)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"
            img = AsyncImage(
                source=url,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=False
            )
            img_box.add_widget(img)
        else:
            # Fallback to local random image
            import random
            img_num = random.randint(1, 10)
            img_path = os.path.join(ASSETS_DIR, "去背", f"{img_num:02d}.png")
            from kivy.uix.image import Image
            img_box.add_widget(Image(
                source=img_path,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True
            ))
            
        self.add_widget(img_box)
        
        # Name
        self.add_widget(MDLabel(
            text=recipe_data.get("name", "Unknown Recipe"),
            font_style="H6", # Slightly larger font for title
            font_name='chinese_font',
            halign="center",
            size_hint_y=0.25 # Reduced text area
        ))

class RecipeRecommendationScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation="vertical")
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Custom Branded Toolbar (Style matched to Family/Inventory)
        self.toolbar_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(10), 0, dp(10), 0],
            spacing=dp(10)
        )
        
        self.left_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "member", "icon3.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: MDApp.get_running_app().open_settings(),
            pos_hint={'center_y': 0.5}
        )
        
        self.title_label = MDLabel(
            text=d["rec_recipes"],
            halign="center",
            font_name='chinese_font',
            font_style="H5",
            pos_hint={'center_y': 0.5}
        )
        
        self.right_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "icon11.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: self.fetch_new_recipes(),
            pos_hint={'center_y': 0.5}
        )
        
        self.toolbar_box.add_widget(self.left_btn)
        self.toolbar_box.add_widget(self.title_label)
        self.toolbar_box.add_widget(self.right_btn)
        
        # Background Image (Transparency 70% -> Opacity 30%)
        # Path: TATA/recommendation/background.jpg
        bg_path = os.path.join(ASSETS_DIR, "recommendation", "background.jpg")
        if os.path.exists(bg_path):
            self.bg_image = Image(
                source=bg_path,
                allow_stretch=True,
                keep_ratio=False,
                opacity=0.3
            )
            self.add_widget(self.bg_image)
        
        self.layout.add_widget(self.toolbar_box)
        
        # Content
        self.scroll = MDScrollView()
        self.recipe_list = MDGridLayout(
            cols=1, # Change to 1 for better display of single recommendation
            padding=dp(20),
            spacing=dp(20),
            size_hint_y=None
        )
        self.recipe_list.bind(minimum_height=self.recipe_list.setter('height'))
        self.scroll.add_widget(self.recipe_list)
        self.layout.add_widget(self.scroll)
        
        self.add_widget(self.layout)
        self.loading = False
        
        # Initial Setup
        self.update_theme_colors()
        
        # Initial call to load or show guide
        Clock.schedule_once(lambda dt: self.initial_load(), 0.1)

    def on_enter(self, *args):
        self.update_theme_colors()
        # Refresh logic
        self.initial_load()

    def update_generate_button(self, visible):
        if visible:
            if self.right_btn not in self.toolbar_box.children:
                self.toolbar_box.add_widget(self.right_btn)
        else:
            if self.right_btn in self.toolbar_box.children:
                self.toolbar_box.remove_widget(self.right_btn)

    def initial_load(self):
        if self.loading: return
        try:
            # Check if we already generated today
            today = datetime.now().strftime('%Y-%m-%d')
            content = database.get_daily_recipes(today)
            
            if content:
                try:
                    data = json.loads(content)
                    self.display_recipes(data)
                except:
                    # JSON error, allow retry
                    self.show_empty_guide()
            else:
                # No data for today, show guide
                self.show_empty_guide()
        except Exception as e:
            print(f"[Recipes] initial_load error: {e}")
            self.show_empty_guide()

    def show_empty_guide(self):
        self.recipe_list.clear_widgets()
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        guide_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(40),
            size_hint_y=None,
            height=dp(300)
        )
        # Using a name for searching later or just clearing
        guide_box.name = "empty_guide"
        
        icon = MDIcon(
            icon="silverware-variant",
            halign="center",
            font_size=dp(64),
            theme_text_color="Secondary"
        )
        msg = MDLabel(
            text=d.get("rec_recipe_hint", "點擊右上方圖示\n為您生成今日專屬食譜"),
            halign="center",
            font_name='chinese_font',
            theme_text_color="Secondary"
        )
        guide_box.add_widget(icon)
        guide_box.add_widget(msg)
        self.recipe_list.add_widget(guide_box)
        self.update_generate_button(True)

    def update_theme_colors(self):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.md_bg_color = [0.1, 0.1, 0.1, 1] if is_dark else COLOR_BG_CREAM
            
        if hasattr(self, 'title_label'):
            self.title_label.theme_text_color = "Custom"
            self.title_label.text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY
            
        self.md_bg_color = [0.05, 0.05, 0.05, 1] if is_dark else COLOR_BG_CREAM

    def fetch_new_recipes(self):
        if self.loading: return
        self.loading = True
        
        self.recipe_list.clear_widgets()

        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Show loading spinner
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(46), dp(46)),
            pos_hint={'center_x': .5, 'center_y': .5},
            active=True
        )
        self.loading_lbl = MDLabel(
            text=d["gen_recipe_msg"],
            halign="center",
            font_name='chinese_font',
            pos_hint={'center_x': .5, 'center_y': .4}
        )
        
        self.loading_box = FloatLayout(size_hint=(1, 1))
        self.loading_box.add_widget(self.spinner)
        self.loading_box.add_widget(self.loading_lbl)
        
        # Add to main screen to overlay everything
        self.add_widget(self.loading_box)
        
        family_data = database.get_family_members()
        equipment_data = database.get_kitchen_equipment()
        inventory_data = database.get_all_inventory()
        ai_manager.get_daily_recipe_recommendations_async(self.on_recipes_generated, family_data, equipment_data, inventory_data)

    def on_recipes_generated(self, result):
        if result and "recipes" in result:
            today = datetime.now().strftime('%Y-%m-%d')
            # Save raw result first (without local image path)
            database.save_daily_recipes(today, json.dumps(result))
            
            # Check for image keywords and preload
            recipes = result.get("recipes", [])
            if recipes:
                r = recipes[0]
                keywords = r.get("image_keywords")
                if keywords:
                    # Update loading text
                    self.loading_lbl.text = "AI正在繪製美味料理中..."
                    # Start download
                    ai_manager.download_recipe_image_async(lambda path: self.on_image_ready(result, path), keywords)
                    return

            # No keywords or no recipes, display immediately
            self.display_recipes(result)
            self.loading = False
            if hasattr(self, 'loading_box'):
                try:
                    self.remove_widget(self.loading_box)
                except:
                    pass

        else:
            self.loading = False
            if hasattr(self, 'loading_box'):
                try:
                    self.remove_widget(self.loading_box)
                except:
                    pass
            
            from kivymd.toast import toast
            toast("AI 生成失敗，請點選右上角重新整理")
            self.show_empty_guide()

    def on_image_ready(self, result, image_path):
        # Inject local path into result for display
        if image_path and result and "recipes" in result:
             result["recipes"][0]["local_image_path"] = image_path
             
        self.display_recipes(result)
        self.loading = False
        if hasattr(self, 'loading_box'):
            try:
                self.remove_widget(self.loading_box)
            except:
                pass

    def add_to_shopping_list(self, recipe_data):
        # 1. Get Unified Items from recipe (same logic as display)
        raw_ings = recipe_data.get("ingredients", [])
        raw_shop = recipe_data.get("shopping_list", [])
        
        unique_items = {}
        for i in (raw_ings or []) + (raw_shop or []):
            name = i.get("name") if isinstance(i, dict) else str(i)
            if not name: continue
            if name not in unique_items:
                unique_items[name] = i if isinstance(i, dict) else {"name": name, "qty": 1, "unit": "unit"}

        # 2. Get Inventory and compare
        inventory = database.get_all_inventory()
        added_count = 0
        
        try:
            for name, data in unique_items.items():
                item_name = data.get("name")
                item_qty = data.get("qty", 1)
                item_unit = data.get("unit", "unit")
                
                # Check stock (similar logic as show_recipe_detail)
                stock_qty = 0
                for inv in inventory:
                    inv_name = str(inv[1]).strip().lower()
                    if item_name.strip().lower() in inv_name or inv_name in item_name.strip().lower():
                        stock_qty += inv[2]
                
                # If stock is insufficient, add to shopping list
                if stock_qty < (item_qty if isinstance(item_qty, (int, float)) else 1):
                    database.add_shopping_item(item_name, str(item_qty), item_unit)
                    added_count += 1
            
            from kivymd.toast import toast
            if added_count > 0:
                toast(f"成功將 {added_count} 項缺漏食材加入清單")
            else:
                toast("庫存充足，無需加入採買清單")
        except Exception as e:
            print(f"DB Error: {e}")
            from kivymd.toast import toast
            toast(f"加入失敗: {str(e)[:20]}...")
            
        if hasattr(self, 'detail_dialog'):
            self.detail_dialog.dismiss()

    def add_single_item_to_shopping_list(self, name, qty, unit):
        try:
            database.add_shopping_item(name, str(qty), unit)
            from kivymd.toast import toast
            toast(f"已加入: {name}")
        except Exception as e:
            print(f"DB Error: {e}")
            from kivymd.toast import toast
            toast(f"加入失敗: {str(e)[:20]}...")

    def cooked_recipe(self, recipe_data):
        # Open dialog to confirm inventory deduction
        ingredients = recipe_data.get("ingredients", [])
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        text = "確認已烹飪此料理？\n系統將自動從庫存扣除食材。\n\n所需食材:"
        
        display_ings = []
        for i in ingredients:
            if isinstance(i, dict):
                display_ings.append(f"{i.get('name')} {i.get('qty')}{i.get('unit')}")
            else:
                display_ings.append(str(i))
                
        if display_ings:
            text += "\n" + "\n".join(display_ings[:5])
            if len(display_ings) > 5: text += "\n..."
            
        self.cook_dialog = MDDialog(
            title="烹飪完成",
            type="custom",
            content_cls=MDLabel(text=text, font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.cook_dialog.dismiss()),
                MDRaisedButton(text="確認扣除", font_name='chinese_font', on_release=lambda x: self.execute_cook(recipe_data))
            ]
        )
        self.cook_dialog.open()
        
    def execute_cook(self, recipe_data):
        from kivymd.toast import toast
        
        ingredients = recipe_data.get("ingredients", [])
        inventory = database.get_all_inventory()
        # inventory item: id, name, qty, unit, expiry, buy, area
        
        deducted_count = 0
        missing_items = []
        
        for ing in ingredients:
            if not isinstance(ing, dict): continue
            
            # Normalizing AI ingredient values
            ing_name = str(ing.get("name", "")).strip().lower()
            ing_qty = ing.get("qty", 0)
            ing_unit = str(ing.get("unit", "unit")).strip().lower()
            
            # Find in inventory using lenient matching
            found = False
            for inv_item in inventory:
                # inv_item[1] = name, inv_item[3] = unit
                inv_name = str(inv_item[1]).strip().lower()
                inv_unit = str(inv_item[3]).strip().lower() if inv_item[3] else "unit"
                
                # Lenient Match: name check (exact or partial) and unit match
                if ing_name == inv_name or ing_name in inv_name or inv_name in ing_name:
                    if inv_unit == ing_unit:
                        database.update_item_quantity(inv_item[0], -ing_qty)
                        found = True
                        deducted_count += 1
                        break
            
            if not found:
                missing_items.append(ing.get("name"))
        
        msg = f"已扣除 {deducted_count} 項食材。"
        if missing_items:
            msg += f"\n未找到: {', '.join(missing_items[:3])}..."
            
        toast(msg)
        self.cook_dialog.dismiss()
        if hasattr(self, 'detail_dialog'):
            self.detail_dialog.dismiss()

    def display_recipes(self, data):
        self.recipe_list.clear_widgets()
        # Safety Guard: Only show the first recipe if multiple are returned
        recipes = data.get("recipes", [])
        if recipes:
            r = recipes[0]
            card = RecipeCard(recipe_data=r, click_callback=self.show_recipe_detail)
            self.recipe_list.add_widget(card)
        self.update_generate_button(False)

    def show_recipe_detail(self, recipe_data):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        from kivy.uix.scrollview import ScrollView
        content_scroll = ScrollView(size_hint_y=None, height=dp(400))
        layout = MDBoxLayout(orientation="vertical", adaptive_height=True, padding=dp(10), spacing=dp(15))
        
        # Intro
        layout.add_widget(MDLabel(text=recipe_data.get("intro", ""), font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True))
        
        # Calories
        layout.add_widget(MDLabel(text=f"{d['calories_estimate']}: {recipe_data.get('calories', 0)} kcal", bold=True, font_name='chinese_font', adaptive_height=True))
        
        # Get Current Inventory
        inventory = database.get_all_inventory()
        # inventory item: id, name, qty, unit, expiry, buy, area
        
        # Combine ingredients and shopping_list from AI (AI often repeats them, we unify)
        raw_ings = recipe_data.get("ingredients", [])
        raw_shop = recipe_data.get("shopping_list", [])
        
        # Create a unified list of unique ingredient names to check
        unique_items = {}
        for i in raw_ings + raw_shop:
            name = i.get("name") if isinstance(i, dict) else str(i)
            if not name: continue
            if name not in unique_items:
                unique_items[name] = i if isinstance(i, dict) else {"name": name, "qty": 1, "unit": "unit"}

        in_stock_items = []
        missing_items = []

        for name, data in unique_items.items():
            item_name = data.get("name")
            item_qty = data.get("qty", 1)
            item_unit = data.get("unit", "unit")
            
            # Find in inventory
            stock_qty = 0
            found_unit = item_unit
            for inv in inventory:
                inv_name = str(inv[1]).strip().lower()
                if item_name.strip().lower() in inv_name or inv_name in item_name.strip().lower():
                    stock_qty += inv[2]
                    found_unit = inv[3] or item_unit
            
            if stock_qty >= (item_qty if isinstance(item_qty, (int, float)) else 1):
                in_stock_items.append({"data": data, "stock": stock_qty, "stock_unit": found_unit})
            else:
                missing_items.append({"data": data, "stock": stock_qty, "stock_unit": found_unit})

        # --- Display Sections ---
        
        # 1. Need to Buy Section
        header_missing = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10))
        header_missing.add_widget(MDIcon(icon="cart-outline", theme_text_color="Custom", text_color=[0.8, 0, 0, 1], size_hint=(None, None), size=(dp(24), dp(24))))
        header_missing.add_widget(MDLabel(text="待採買食材", font_style="H6", font_name='chinese_font', adaptive_height=True, text_color=[0.8, 0, 0, 1], theme_text_color="Custom"))
        layout.add_widget(header_missing)
        if not missing_items:
            layout.add_widget(MDLabel(text="• 目前無缺少的食材", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True))
        else:
            for item in missing_items:
                data = item["data"]
                row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(5))
                status_icon = MDIcon(icon="alert-circle-outline", theme_text_color="Custom", text_color=[0.8, 0, 0, 1], size_hint=(None, None), size=(dp(24), dp(24)), pos_hint={'center_y': 0.5})
                
                name_lbl = MDLabel(text=f"{data['name']} {data['qty']}{data['unit']}", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True, pos_hint={'center_y': 0.5})
                
                row.add_widget(status_icon)
                row.add_widget(name_lbl)
                layout.add_widget(row)

        # 2. In Stock Section
        header_stock = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10), padding=[0, dp(15), 0, 0])
        header_stock.add_widget(MDIcon(icon="check-circle-outline", theme_text_color="Custom", text_color=[0, 0.6, 0, 1], size_hint=(None, None), size=(dp(24), dp(24))))
        header_stock.add_widget(MDLabel(text="已擁有庫存", font_style="H6", font_name='chinese_font', adaptive_height=True, text_color=[0, 0.6, 0, 1], theme_text_color="Custom"))
        layout.add_widget(header_stock)
        if not in_stock_items:
            layout.add_widget(MDLabel(text="• 目前無現成庫存", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True))
        else:
            for item in in_stock_items:
                data = item["data"]
                row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(5))
                status_icon = MDIcon(icon="check-circle", theme_text_color="Custom", text_color=[0, 0.7, 0, 1], size_hint=(None, None), size=(dp(24), dp(24)), pos_hint={'center_y': 0.5})
                
                stock_text = f" (庫存: {item['stock']}{item['stock_unit']})"
                name_lbl = MDLabel(text=f"{data['name']} {data['qty']}{data['unit']}{stock_text}", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True, pos_hint={'center_y': 0.5})
                
                row.add_widget(status_icon)
                row.add_widget(name_lbl)
                layout.add_widget(row)

        # 3. Steps
        header_steps = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10), padding=[0, dp(15), 0, 0])
        header_steps.add_widget(MDIcon(icon="format-list-bulleted", size_hint=(None, None), size=(dp(24), dp(24))))
        header_steps.add_widget(MDLabel(text="烹飪步驟", font_style="H6", font_name='chinese_font', adaptive_height=True))
        layout.add_widget(header_steps)
        steps_text = "\n\n".join([f"{i+1}. {s}" for i, s in enumerate(recipe_data.get("steps", []))])
        layout.add_widget(MDLabel(text=steps_text, font_name='chinese_font', adaptive_height=True))

        
        content_scroll.add_widget(layout)
        
        self.detail_dialog = MDDialog(
            title=recipe_data.get("name", d["recipe_title"]),
            type="custom",
            content_cls=content_scroll,
            buttons=[
                MDFlatButton(text="加入採買", font_name='chinese_font', theme_text_color="Custom", text_color=[0, 0.5, 0, 1], on_release=lambda x: self.add_to_shopping_list(recipe_data)),
                MDFlatButton(text="我煮了這道", font_name='chinese_font', theme_text_color="Custom", text_color=[1, 0.5, 0, 1], on_release=lambda x: self.cooked_recipe(recipe_data)),
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.detail_dialog.dismiss())
            ]
        )
        self.detail_dialog.open()
