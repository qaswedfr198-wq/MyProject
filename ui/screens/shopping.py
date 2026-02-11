from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFloatingActionButton, MDRaisedButton, MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, ILeftBodyTouch, IRightBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.metrics import dp
import os
import database
import ai_manager
import threading
from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_ACCENT_SAGE, COLOR_TEXT_DARK_GREY

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'TATA'))

class ListItemWithCheckbox(OneLineAvatarIconListItem):
    # Custom list item with Checkbox on left and Delete on right
    def __init__(self, item_id, is_checked, delete_callback, toggle_callback, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.ids._right_container.width = dp(50) # Adjust right container for icon
        self.ids._left_container.width = dp(50)  # Adjust left container for checkbox
        
        # Checkbox (Left)
        self._checkbox = MDCheckbox(active=is_checked, pos_hint={'center_y': .5})
        self._checkbox.bind(active=lambda x, val: toggle_callback(self.item_id, val))
        self.add_widget(self._checkbox) # Add directly, customization for LeftBody might be tricky with pure Python
        # KivyMD's OneLineAvatarIconListItem usually expects standard containers. 
        # Making a cleaner implementation below using standard componentsContainer
        
class ShoppingListItem(MDBoxLayout):
    def __init__(self, item_data, toggle_callback, delete_callback, edit_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = [dp(10), 0]
        self.spacing = dp(5)
        self.item_data = item_data # id, name, qty, checked, unit
        
        # Checkbox
        self.checkbox = MDCheckbox(
            active=(item_data[3] == 1),
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_y': 0.5}
        )
        self.checkbox.bind(active=lambda x, val: toggle_callback(item_data[0], val))
        self.add_widget(self.checkbox)
        
        # Name Area (Clickable)
        self.content_btn = MDFlatButton(
            text=str(item_data[1]),
            font_name='chinese_font',
            size_hint_x=1,
            pos_hint={'center_y': 0.5},
            on_release=lambda x: edit_callback(item_data)
        )
        # Force left alignment for the button text
        self.content_btn.halign = 'left'
        self.add_widget(self.content_btn)
        
        # Qty Area (Clickable)
        qty_val = str(item_data[2]) if item_data[2] else "1"
        unit_val = str(item_data[4]) if len(item_data) > 4 and item_data[4] and item_data[4] != 'unit' else ""
        qty_display = f"{qty_val} {unit_val}".strip()
        
        self.qty_btn = MDFlatButton(
            text=qty_display,
            font_name='chinese_font',
            size_hint_x=None,
            width=dp(80), # Increased width for unit
            pos_hint={'center_y': 0.5},
            theme_text_color="Secondary",
            on_release=lambda x: edit_callback(item_data)
        )
        self.add_widget(self.qty_btn)
        
        # Delete Button
        self.del_btn = MDIconButton(
            icon="trash-can-outline",
            pos_hint={'center_y': 0.5},
            on_release=lambda x: delete_callback(item_data[0])
        )
        self.add_widget(self.del_btn)

class ShoppingListContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        
        # Helper to get lang
        self.app = MDApp.get_running_app()
        self.d = LANG_DICT[self.app.current_lang]
        
        # Control Bar
        self.control_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            padding=[dp(10), 0],
            spacing=dp(10)
        )
        
        # Select All Checkbox
        self.select_all_chk = MDCheckbox(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_y': 0.5}
        )
        self.select_all_chk.bind(active=self.on_select_all)
        
        self.select_all_lbl = MDLabel(
            text="全選", # Localization needed
            font_name='chinese_font',
            pos_hint={'center_y': 0.5},
            theme_text_color="Primary"
        )
        
        # Add to Inventory Button (Icon Button)
        self.add_inv_btn = MDIconButton(
            icon="basket-plus",
            pos_hint={'center_y': 0.5},
            on_release=lambda x: self.add_to_inventory_dialog()
        )
        
        # Delete Selected Button
        self.del_selected_btn = MDIconButton(
            icon="delete-sweep", # More standard icon name
            theme_text_color="Custom",
            text_color=[0.8, 0, 0, 1],
            pos_hint={'center_y': 0.5},
            on_release=lambda x: self.delete_selected_items()
        )
        
        self.control_bar.add_widget(self.select_all_chk)
        self.control_bar.add_widget(self.select_all_lbl)
        
        # Spacer logic: Use a Widget with size_hint_x=1 to push remaining items to the right
        from kivy.uix.widget import Widget
        spacer = Widget()
        self.control_bar.add_widget(spacer)
        
        self.control_bar.add_widget(self.add_inv_btn)
        self.control_bar.add_widget(self.del_selected_btn)
        
        self.add_widget(self.control_bar)
        
        # Content Scroll
        self.scroll = MDScrollView()
        self.list_layout = MDBoxLayout(orientation='vertical', size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        
        self.add_widget(self.scroll)
        self.load_data()

    def on_select_all(self, checkbox, value):
        # Update all items
        items = database.get_shopping_list()
        for item in items:
            # item: id, name, qty, is_checked, unit
            if (value and item[3] == 0) or (not value and item[3] == 1):
                database.update_shopping_item_status(item[0], 1 if value else 0)
        self.load_data()

    def delete_selected_items(self):
        # 1. Check if any items are selected
        items = database.get_shopping_list()
        checked_items = [i for i in items if i[3] == 1]
        
        if not checked_items:
            from kivymd.toast import toast
            toast("請先勾選要刪除的項目")
            return
            
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.bulk_del_dialog = MDDialog(
            title="確認刪除",
            type="custom",
            content_cls=MDLabel(text=f"確定要刪除這 {len(checked_items)} 個項目嗎？", font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.bulk_del_dialog.dismiss()),
                MDFlatButton(text="確定刪除", font_name='chinese_font', theme_text_color="Custom", text_color=[0.8, 0, 0, 1], 
                             on_release=lambda x: self.execute_bulk_delete()),
            ]
        )
        self.bulk_del_dialog.open()

    def execute_bulk_delete(self):
        database.delete_checked_shopping_items()
        self.bulk_del_dialog.dismiss()
        self.load_data()
        from kivymd.toast import toast
        toast("已刪除選取項目")

    def load_data(self):
        self.list_layout.clear_widgets()
        items = database.get_shopping_list()
        
        is_dark = self.app.theme_cls.theme_style == "Dark"
        text_color = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        
        # Check if all selected to update header checkbox state without triggering event
        all_checked = all(i[3] == 1 for i in items) if items else False
        self.select_all_chk.active = all_checked
        
        if not items:
            self.empty_label = MDLabel(
                text="清單是空的", # Localization needed
                halign="center",
                theme_text_color="Custom",
                text_color=text_color,
                font_name='chinese_font',
                size_hint_y=None,
                height=dp(100)
            )
            self.list_layout.add_widget(self.empty_label)
        else:
            for item in items:
                row = ShoppingListItem(item, self.toggle_item, self.delete_item, self.show_edit_dialog)
                self.list_layout.add_widget(row)

    def show_edit_dialog(self, item_data):
        # item_data: id, name, qty, checked, unit
        self.edit_item_content = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None, height="180dp")
        self.edit_name_field = MDTextField(text=str(item_data[1]), hint_text="項目名稱", font_name='chinese_font')
        self.edit_qty_field = MDTextField(text=str(item_data[2]), hint_text="數量 (數字)", font_name='chinese_font')
        self.edit_unit_field = MDTextField(text=str(item_data[4]) if len(item_data) > 4 and item_data[4] else "", 
                                          hint_text="單位 (例如: g, ml, 個)", font_name='chinese_font')
        
        self.edit_item_content.add_widget(self.edit_name_field)
        self.edit_item_content.add_widget(self.edit_qty_field)
        self.edit_item_content.add_widget(self.edit_unit_field)
        
        self.edit_dialog = MDDialog(
            title="修改項目",
            type="custom",
            content_cls=self.edit_item_content,
            buttons=[
                MDFlatButton(text=self.d["cancel"], font_name='chinese_font', on_release=lambda x: self.edit_dialog.dismiss()),
                MDRaisedButton(text="更新", font_name='chinese_font', on_release=lambda x: self.save_edit_item(item_data[0]))
            ]
        )
        self.edit_dialog.open()

    def save_edit_item(self, item_id):
        name = self.edit_name_field.text
        qty = self.edit_qty_field.text
        unit = self.edit_unit_field.text
        if not name: return
        
        database.update_shopping_item(item_id, name=name, quantity=qty, unit=unit)
        self.edit_dialog.dismiss()
        self.load_data()

    def toggle_item(self, item_id, is_checked):
        database.update_shopping_item_status(item_id, is_checked)
        # Check if all selected
        items = database.get_shopping_list()
        all_checked = all(i[3] == 1 for i in items) if items else False
        if self.select_all_chk.active != all_checked:
             # Prevent recursion loop if binding is strict, but usually click triggers only
             self.select_all_chk.active = all_checked

    def delete_item(self, item_id):
        database.delete_shopping_item(item_id)
        self.load_data()

    def show_add_dialog(self, instance=None):
        self.add_item_content = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None, height="120dp")
        self.name_field = MDTextField(hint_text="項目名稱", font_name='chinese_font')
        self.qty_field = MDTextField(hint_text="數量 (例如: 2, 300g)", font_name='chinese_font')
        
        self.add_item_content.add_widget(self.name_field)
        self.add_item_content.add_widget(self.qty_field)
        
        self.dialog = MDDialog(
            title="新增採買項目",
            type="custom",
            content_cls=self.add_item_content,
            buttons=[
                MDFlatButton(text=self.d["cancel"], font_name='chinese_font', on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text=self.d["save"], font_name='chinese_font', on_release=self.save_new_item)
            ]
        )
        self.dialog.open()

    def save_new_item(self, *args):
        name = self.name_field.text
        if not name: return
        
        qty = self.qty_field.text
        database.add_shopping_item(name, qty)
        self.dialog.dismiss()
        self.load_data()

    def add_to_inventory_dialog(self):
        # 1. Get Checked Items from DB directly to be safe
        items = database.get_shopping_list()
        checked_items = [i for i in items if i[3] == 1]
        
        if not checked_items:
            from kivymd.toast import toast
            toast("請先勾選已購買的項目")
            return
            
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        text = f"確認將 {len(checked_items)} 個項目加入庫存嗎？\n(將自動設為今日購買，預設7天過期)"
        
        self.inv_dialog = MDDialog(
            title="一鍵入庫",
            type="custom",
            content_cls=MDLabel(text=text, font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.inv_dialog.dismiss()),
                MDRaisedButton(text="確認入庫", font_name='chinese_font', on_release=lambda x: self.execute_add_to_inventory(checked_items))
            ]
        )
        self.inv_dialog.open()

    def execute_add_to_inventory(self, checked_items):
        from kivymd.toast import toast
        toast("正在AI智慧入庫中，請稍候...")
        self.inv_dialog.dismiss()
        
        # Run in background to avoid freezing UI
        threading.Thread(target=self._background_add_inventory, args=(checked_items,), daemon=True).start()

    def _background_add_inventory(self, checked_items):
        from datetime import datetime, timedelta
        import re
        from kivy.clock import Clock
        
        today = datetime.now().strftime("%Y-%m-%d")
        expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d") # Default 7 days
        
        for item in checked_items:
            # item: id, name, qty, is_checked, unit
            name = item[1]
            qty_str = item[2]
            
            qty_val = 1
            unit_val = "unit" # Default
            
            # Try to parse "300g", "1.5kg" etc.
            # Regex for number (int/float) followed by optional unit
            match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)?", str(qty_str))
            
            # Check if unit column is available (structured data)
            col_unit = item[4] if len(item) > 4 and item[4] else None
            
            if match:
                try:
                    qty_raw = float(match.group(1))
                    unit_raw = match.group(2) or col_unit # Use col_unit if regex didn't find one
                    
                    if unit_raw:
                        unit_raw = str(unit_raw).lower()
                        if unit_raw in ['kg', 'kilogram']:
                            qty_val = int(qty_raw * 1000)
                            unit_val = 'g'
                        elif unit_raw in ['g', 'gram']:
                            qty_val = int(qty_raw)
                            unit_val = 'g'
                        elif unit_raw in ['l', 'liter']:
                            qty_val = int(qty_raw * 1000)
                            unit_val = 'ml'
                        elif unit_raw in ['ml']:
                            qty_val = int(qty_raw)
                            unit_val = 'ml'
                        else:
                            qty_val = int(qty_raw)
                            unit_val = 'unit' # Unknown unit treated as count
                    else:
                        qty_val = int(qty_raw)
                        unit_val = 'unit'
                except:
                    pass
            elif col_unit:
                unit_val = str(col_unit).lower()
                # If no match but has col_unit, maybe it's just a number in qty_str
                try: qty_val = int(float(qty_str))
                except: pass
            
            # AI Auto Categorization
            area = ai_manager.estimate_item_category(name)
            
            # Add to inventory with UNIT
            database.add_inventory_item(name, qty_val, unit_val, expiry, today, area)
            
            # Delete from shopping list
            database.delete_shopping_item(item[0])
            
        # Callback to UI thread
        Clock.schedule_once(self._on_inventory_add_complete, 0)

    def _on_inventory_add_complete(self, dt):
        self.load_data()
        from kivymd.toast import toast
        toast("已完成AI智慧分類入庫！")

class ShoppingScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        self.content = ShoppingListContent()
        
        self.main_float = MDBoxLayout(orientation='vertical')
        self.overlay = FloatLayout()
        
        # Add Item FAB
        self.add_fab = MDFloatingActionButton(
            icon="plus",
            type="standard",
            md_bg_color=COLOR_ACCENT_SAGE,
            icon_color=[1, 1, 1, 1],
            elevation=0,
            pos_hint={"right": 0.95, "bottom": 0.05}
        )
        self.add_fab.bind(on_release=self.content.show_add_dialog)
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Toolbar
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
            text="採買清單", 
            halign="center",
            font_name='chinese_font',
            font_style="H5",
            pos_hint={'center_y': 0.5}
        )
        
        # Removed Right Button (Moved to Content)
        
        self.toolbar_box.add_widget(self.left_btn)
        self.toolbar_box.add_widget(self.title_label)
        self.toolbar_box.add_widget(MDBoxLayout(size_hint_x=None, width=dp(60))) # Spacer for balance
        
        self.main_float.add_widget(self.toolbar_box)
        self.main_float.add_widget(self.content)

        
        # Background
        self.bg_image = Image(
            source=os.path.join(ASSETS_DIR, "stock", "stockbackground.png"), # Reuse stock background
            allow_stretch=True,
            keep_ratio=False,
            opacity=0.4,
            size_hint=(1, 1)
        )
        self.add_widget(self.bg_image)
        self.add_widget(self.main_float)
        self.add_widget(self.overlay)
        self.overlay.add_widget(self.add_fab)
        
        self.update_theme_colors()

    def update_theme_colors(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        self.md_bg_color = bg_color
        
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else COLOR_BG_CREAM
            
        if hasattr(self, 'title_label'):
            self.title_label.theme_text_color = "Custom"
            self.title_label.text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY
            
        if hasattr(self, 'add_fab'):
            self.add_fab.md_bg_color = COLOR_ACCENT_SAGE

    def on_enter(self, *args):
        self.content.load_data()

    def add_to_inventory_dialog(self):
        # 1. Get Checked Items from DB directly to be safe
        # Logic is similar but needs to call execute via database
        items = database.get_shopping_list()
        checked_items = [i for i in items if i[3] == 1]
        
        if not checked_items:
            from kivymd.toast import toast
            toast("請先勾選已購買的項目")
            return
            
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        text = f"確認將 {len(checked_items)} 個項目加入庫存嗎？\n(將自動設為今日購買，預設7天過期)"
        
        self.inv_dialog = MDDialog(
            title="一鍵入庫",
            type="custom",
            content_cls=MDLabel(text=text, font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.inv_dialog.dismiss()),
                MDRaisedButton(text="確認入庫", font_name='chinese_font', on_release=lambda x: self.execute_add_to_inventory(checked_items))
            ]
        )
        self.inv_dialog.open()


    def execute_add_to_inventory(self, checked_items):
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime("%Y-%m-%d")
        expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d") # Default 7 days
        
        for item in checked_items:
            # item: id, name, qty, checked, unit
            name = item[1]
            qty_str = item[2]
            
            # Try to parse qty as int, otherwise default 1 and append original qty string to name if complex?
            # Or just use qty=1 for now since inventory expects INT.
            # Improvement: Inventory should accept String qty or we parse.
            # LocalDB add_inventory_item expects INT quantity.
            
            import re
            qty_val = 1
            try:
                # Find first number
                nums = re.findall(r'\d+', qty_str)
                if nums:
                    qty_val = int(nums[0])
            except:
                pass
                
            # Add to inventory
            database.add_inventory_item(name, qty_val, expiry, today, "一般") # Default area 'General'
            
            # Delete from shopping list
            database.delete_shopping_item(item[0])
            
        self.inv_dialog.dismiss()
        self.load_data()
        
        from kivymd.toast import toast
        toast("已成功入庫！")
