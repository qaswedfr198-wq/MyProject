from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFloatingActionButton, MDRaisedButton, MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock
import os
import ai_manager
import database
from datetime import datetime
from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_ACCENT_SAGE, COLOR_TEXT_DARK_GREY
from ui.cards import InventoryCard

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'TATA'))

class InventoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.selected_items = set() # Track selected item IDs for bulk delete
        self.menu = None # Dropdown menu for adding items

        self.layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        # Category Filter Bar
        self.filter_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=0, 
            padding=0, 
            size_hint_y=None,
            height=dp(48) # Fixed height for the bar
        )
        self.layout.add_widget(self.filter_layout)
        
        # Default category
        self.current_category = "general" # Key in LANG_DICT
        self.categories = ["general", "cat_frozen", "cat_fridge", "cat_dry", "cat_seasoning"]
        
        self.scroll = MDScrollView()
        self.list_layout = MDList()
        self.scroll.add_widget(self.list_layout)
        
        self.layout.add_widget(self.scroll)
        
        self.main_float = MDBoxLayout(orientation='vertical')
        
        self.overlay = FloatLayout()
        
        # Camera FAB removed and merged into top-right menu
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Custom Branded Toolbar to allow larger icons (Style matched to FamilyScreen)
        self.toolbar_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(10), 0, dp(10), 0],
            spacing=dp(10)
        )
        
        # Shopping List Button (Now on the Left)
        self.shop_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "stock", "buy.png"),
            icon_size=dp(56), 
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=self.show_shopping_dialog,
            pos_hint={'center_y': 0.5}
        )
        self.toolbar_box.add_widget(self.shop_btn)
        
        self.title_label = MDLabel(
            text=d["inventory"],
            halign="center",
            font_name='chinese_font',
            font_style="H5",
            pos_hint={'center_y': 0.5},
            size_hint_x=1, # Take available space
            shorten=True,  # Prevent wrap
            max_lines=1
        )
        self.toolbar_box.add_widget(self.title_label)
        
        # Right Button (Add Item)
        self.right_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "stock", "reg.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=self.open_menu,
            pos_hint={'center_y': 0.5}
        )
        self.toolbar_box.add_widget(self.right_btn)
        
        self.main_float.add_widget(self.toolbar_box)
        self.main_float.add_widget(self.layout)
        
        # self.overlay.add_widget(self.cam_fab) # Removed
        # Custom Background Image
        self.bg_image = Image(
            source=os.path.join(ASSETS_DIR, "stock", "stockbackground.png"),
            allow_stretch=True,
            keep_ratio=False,
            opacity=0.4,
            size_hint=(1, 1)
        )
        self.add_widget(self.bg_image)
        
        self.add_widget(self.main_float)
        self.add_widget(self.overlay)

        # Batch Delete Button (Hidden initially)
        self.batch_delete_btn = MDFillRoundFlatButton(
            text="批量刪除 (0)",
            md_bg_color=[0.8, 0.2, 0.2, 1],
            font_name='chinese_font',
            pos_hint={'center_x': 0.5, 'y': 0.2},
            opacity=0,
            disabled=True,
            on_release=self.confirm_bulk_delete
        )
        self.overlay.add_widget(self.batch_delete_btn)

        self.update_theme_colors()
        self.refresh_filter_buttons() # Create buttons
        self.update_theme_colors()
        self.refresh_filter_buttons() # Create buttons
        self.load_data()

    def on_enter(self, *args):
        self.load_data()
        
    def refresh_filter_buttons(self):
        self.filter_layout.clear_widgets()
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        is_dark = app.theme_cls.theme_style == "Dark"
        
        for cat_key in self.categories:
            is_active = (cat_key == self.current_category)
            
            # Active color
            if is_active:
                bg_color = [0.3, 0.5, 0.3, 1] if is_dark else COLOR_ACCENT_SAGE
                text_color = [1, 1, 1, 1]
            else:
                 # Inactive
                bg_color = [0.2, 0.2, 0.2, 1] if is_dark else [0.9, 0.9, 0.9, 1]
                text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY

            btn = MDRaisedButton(
                text=d[cat_key],
                md_bg_color=bg_color,
                text_color=text_color,
                font_name='chinese_font',
                size_hint=(1, 1), # Equal weight
                size_hint_min_x=0, # Allow shrinking freely
                elevation=1, 
                pos_hint={'center_y': 0.5} 
            )
            # Set radius property after creation to avoid __init__ issues
            btn.radius = [0, 0, 0, 0] # Square corners
            
            # Bind with closure
            btn.bind(on_release=lambda x, k=cat_key: self.set_category(k))
            self.filter_layout.add_widget(btn)

    def set_category(self, cat_key):
        self.current_category = cat_key
        self.refresh_filter_buttons()
        self.load_data()
        
    def update_theme_colors(self, *args):
        is_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        self.md_bg_color = bg_color
        # if hasattr(self, 'main_float'):
        #     self.main_float.md_bg_color = bg_color
            
        # Refresh filter buttons to pick up new theme colors
        if hasattr(self, 'filter_layout') and self.filter_layout.children:
             self.refresh_filter_buttons()
            
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else COLOR_BG_CREAM
            
        if hasattr(self, 'title_label'):
            self.title_label.theme_text_color = "Custom"
            self.title_label.text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY
            
        # self.cam_fab removed

        if hasattr(self, 'empty_label') and self.empty_label:
            text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]
            self.empty_label.theme_text_color = "Custom"
            self.empty_label.text_color = text_color

    def load_data(self):
        self.list_layout.clear_widgets()
        self.selected_items.clear()
        self.update_batch_delete_btn()
        items = database.get_all_inventory()
        
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        d = LANG_DICT[app.current_lang]
        
        text_color = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        secondary_color = [0.9, 0.9, 0.9, 1] if is_dark else [0.6, 0.6, 0.6, 1]
        
        if not items:
            if not hasattr(self, 'empty_label'):
                self.empty_label = MDLabel(
                    text=d["no_items"], 
                    halign="center", 
                    theme_text_color="Custom", 
                    text_color=text_color,
                    font_name='chinese_font',
                    pos_hint={'center_x': 0.5, 'center_y': 0.7}
                )
            else:
                self.empty_label.text = d["no_items"]
                self.empty_label.text_color = text_color
                
            if self.empty_label not in self.overlay.children:
                self.overlay.add_widget(self.empty_label)
            return

        # If items exist, ensure label is removed
        if hasattr(self, 'empty_label') and self.empty_label in self.overlay.children:
            self.overlay.remove_widget(self.empty_label)

        # Filter items
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        target_area_name = d[self.current_category] # e.g. "冷凍" or "Frozen"
        
        filtered_items = []
        for item in items:
            # item structure: item_id, name, qty, expiry_date, buy_date, area
            # item structure: item_id, name, qty, unit, expiry_date, buy_date, area
            area = item[6]
            if area == target_area_name:
                filtered_items.append(item)
        
        items = filtered_items 

        if not items:
            if not hasattr(self, 'empty_label'):
                self.empty_label = MDLabel(
                    text=d["no_items"], 
                    halign="center", 
                    theme_text_color="Custom", 
                    text_color=text_color,
                    font_name='chinese_font',
                    pos_hint={'center_x': 0.5, 'center_y': 0.7}
                )
            else:
                self.empty_label.text = d["no_items"]
                self.empty_label.text_color = text_color
                
            if self.empty_label not in self.overlay.children:
                self.overlay.add_widget(self.empty_label)
            return

        # If items exist, ensure label is removed
        if hasattr(self, 'empty_label') and self.empty_label in self.overlay.children:
            self.overlay.remove_widget(self.empty_label)

        for item in items:
            card = InventoryCard(
                item_data=item,
                delete_callback=self.confirm_delete,
                checkbox_callback=self.on_item_selected,
                edit_callback=self.show_edit_dialog
            )
            self.list_layout.add_widget(card)

    def show_edit_dialog(self, item_data):
        # item_data: item_id, name, qty, unit, expiry_date, buy_date, area
        
        # Use ScrollView for content to prevent overflow
        from kivymd.uix.scrollview import MDScrollView
        
        # Container for fields (scrollable)
        content_box = MDBoxLayout(
            orientation="vertical", 
            spacing="12dp", 
            adaptive_height=True,
            padding=[0, 0, 0, dp(20)] # Bottom padding
        )
        
        # ScrollView constrained height
        scroll = MDScrollView(
            size_hint_y=None,
            height=dp(400) # Fixed visible height for the scroll area
        )
        scroll.add_widget(content_box)
        
        # Store references on self so saving works
        self.edit_item_content = content_box 
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        is_dark = app.theme_cls.theme_style == "Dark"
        
        # Define colors explicitly for input visibility
        text_color_normal = [0.2, 0.2, 0.2, 1] if not is_dark else [0.9, 0.9, 0.9, 1]
        text_color_focus = [0, 0, 0, 1] if not is_dark else [1, 1, 1, 1]
        hint_text_color = [0.5, 0.5, 0.5, 1] if not is_dark else [0.7, 0.7, 0.7, 1]
        line_color = [0.2, 0.2, 0.2, 1] if not is_dark else [0.8, 0.8, 0.8, 1]
        
        def create_field(text, hint, readonly=False):
            return MDTextField(
                text=str(text), 
                hint_text=hint, 
                font_name='chinese_font',
                font_name_hint_text='chinese_font',
                line_color_normal=line_color,
                line_color_focus=COLOR_ACCENT_SAGE,
                text_color_normal=text_color_normal,
                text_color_focus=text_color_focus,
                hint_text_color_normal=hint_text_color,
                hint_text_color_focus=COLOR_ACCENT_SAGE,
                mode="line",
                readonly=readonly
            )

        self.edit_name_field = create_field(item_data[1], "名稱")
        self.edit_name_field.multiline = True # Allow multi line
        
        # Quantity
        val_qty = item_data[2]
        # Unit Logic
        current_unit = item_data[3] if item_data[3] else 'unit'
        
        # Reverse logic to find Type
        type_str = "Quantity" # Default
        if current_unit in ['g', 'kg']:
             type_str = "Weight"
             # If stored as g but display might need adjustment? 
             # For now keep as stored value to avoid complexity, or normalize?
             # Let's show as stored.
        elif current_unit in ['ml', 'l']:
             type_str = "Volume"
             
        # Localized Type Name
        loc_type_map = {
            "Weight": d["u_weight"], 
            "Volume": d["u_volume"], 
            "Quantity": d["u_qty"]
        }
        loc_type_name = loc_type_map.get(type_str, d["u_qty"])
        
        # Localized Unit Name
        unit_label_map = {
            "g": d["unit_g"],
            "kg": d["unit_kg"],
            "ml": d["unit_ml"],
            "l": d["unit_l"],
            "unit": d["unit_pc"]
        }
        loc_unit_name = unit_label_map.get(current_unit, current_unit)

        self.edit_qty_field = create_field(val_qty, "數量 (數字)")
        
        # Unit Type & Unit Fields (Readonly for menu)
        self.edit_unit_type_field = create_field(loc_type_name, d["u_type"], readonly=True)
        self.edit_unit_field = create_field(loc_unit_name, d["u_unit"], readonly=True)
        
        self.edit_unit_type_field.bind(focus=self.on_edit_unit_type_focus)
        self.edit_unit_field.bind(focus=self.on_edit_unit_focus)
        
        self.edit_expiry_field = create_field(item_data[4], "到期日 (YYYY-MM-DD)")
        self.edit_buy_field = create_field(item_data[5] if item_data[5] else "", "購買日 (YYYY-MM-DD)")
        
        # Area Field (Readonly for menu)
        self.edit_area_field = create_field(item_data[6], "區域", readonly=True)
        self.edit_area_field.bind(focus=self.on_edit_area_focus)
        
        # -- Menus for Edit --
        self.edit_unit_type_menu = MDDropdownMenu(
            caller=self.edit_unit_type_field,
            items=[
                {"text": d["u_weight"], "viewclass": "OneLineListItem", "on_release": lambda: self.set_edit_unit_type(d["u_weight"])},
                {"text": d["u_volume"], "viewclass": "OneLineListItem", "on_release": lambda: self.set_edit_unit_type(d["u_volume"])},
                {"text": d["u_qty"], "viewclass": "OneLineListItem", "on_release": lambda: self.set_edit_unit_type(d["u_qty"])},
            ],
            width_mult=4,
        )
        
        # Init Unit Menu
        self.update_edit_unit_menu(type_str)
        
        # -- Area Menu for Edit --
        area_menu_items = []
        # Reuse self.categories if available, or define list
        categories = ["cat_frozen", "cat_fridge", "cat_dry", "cat_seasoning", "cat_general"]
        
        for cat_key in categories:
             area_menu_items.append({
                 "text": d.get(cat_key, cat_key),
                 "viewclass": "OneLineListItem",
                 "on_release": lambda x=d.get(cat_key, cat_key): self.set_edit_area(x),
                 "font_name": "chinese_font"
             })
        
        self.edit_area_menu = MDDropdownMenu(
            caller=self.edit_area_field,
            items=area_menu_items,
            width_mult=4,
        )

        self.edit_item_content.add_widget(self.edit_name_field)
        
        # Qty row
        qty_box = MDBoxLayout(orientation='horizontal', spacing="10dp", adaptive_height=True)
        qty_box.add_widget(self.edit_qty_field)
        qty_box.add_widget(self.edit_unit_type_field)
        qty_box.add_widget(self.edit_unit_field)
        
        self.edit_item_content.add_widget(qty_box)
        self.edit_item_content.add_widget(self.edit_expiry_field)
        self.edit_item_content.add_widget(self.edit_buy_field)
        self.edit_item_content.add_widget(self.edit_area_field)
        
        self.edit_dialog = MDDialog(
            title="修改食材",
            type="custom",
            content_cls=scroll,
            buttons=[
                MDFlatButton(text="取消", font_name='chinese_font', on_release=lambda x: self.edit_dialog.dismiss()),
                MDRaisedButton(text="更新", font_name='chinese_font', on_release=lambda x: self.save_edit_item(item_data[0]))
            ]
        )
        self.edit_dialog.open()

    # --- Edit Dialog Helper Methods ---
    def on_edit_unit_type_focus(self, instance, focused):
        if focused: self.edit_unit_type_menu.open()

    def on_edit_unit_focus(self, instance, focused):
        if focused: self.edit_unit_menu.open()

    def set_edit_unit_type(self, localized_type_name):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        reverse_type_map = {
            d["u_weight"]: "Weight",
            d["u_volume"]: "Volume",
            d["u_qty"]: "Quantity"
        }
        internal_type = reverse_type_map.get(localized_type_name, "Quantity")
        
        self.edit_unit_type_field.text = localized_type_name
        self.edit_unit_type_menu.dismiss()
        self.edit_unit_type_field.focus = False
        self.update_edit_unit_menu(internal_type)

    def update_edit_unit_menu(self, type_name):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        unit_label_map = {
            "g": d["unit_g"],
            "kg": d["unit_kg"],
            "ml": d["unit_ml"],
            "l": d["unit_l"],
            "unit": d["unit_pc"]
        }
        
        units = []
        if type_name == "Weight":
            units = ["g", "kg"]
            self.edit_unit_field.text = d["unit_g"]
        elif type_name == "Volume":
            units = ["ml", "l"]
            self.edit_unit_field.text = d["unit_ml"]
        else:
            units = ["unit"]
            self.edit_unit_field.text = d["unit_pc"]
            
        items = []
        for u in units:
            label = unit_label_map.get(u, u)
            items.append({
                "text": label,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=label: self.set_edit_unit(x)
            })
            
        self.edit_unit_menu = MDDropdownMenu(
            caller=self.edit_unit_field,
            items=items,
            width_mult=2,
        )

    def set_edit_unit(self, unit_name):
        self.edit_unit_field.text = unit_name
        self.edit_unit_menu.dismiss()
        self.edit_unit_field.focus = False

    def on_edit_area_focus(self, instance, focused):
        if focused: self.edit_area_menu.open()

    def set_edit_area(self, area_name):
        self.edit_area_field.text = area_name
        self.edit_area_menu.dismiss()
        self.edit_area_field.focus = False

    def save_edit_item(self, item_id):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        name = self.edit_name_field.text
        # Qty might be empty
        qty_str = self.edit_qty_field.text
        try:
            qty_raw = float(qty_str) if qty_str else 0
        except:
            qty_raw = 0
            
        expiry = self.edit_expiry_field.text
        buy = self.edit_buy_field.text
        area = self.edit_area_field.text
        
        if not name: return
        
        # Unit Conversion Logic
        reverse_unit_map = {
            d["unit_g"]: "g",
            d["unit_kg"]: "kg",
            d["unit_ml"]: "ml",
            d["unit_l"]: "l",
            d["unit_pc"]: "unit"
        }
        unit_val = reverse_unit_map.get(self.edit_unit_field.text, "unit")
        
        # Normalization (kg->g, l->ml)
        final_qty = int(qty_raw)
        final_unit = unit_val
        
        if unit_val == 'kg':
             final_qty = int(qty_raw * 1000)
             final_unit = 'g'
        elif unit_val == 'l':
             final_qty = int(qty_raw * 1000)
             final_unit = 'ml'
        elif unit_val == 'g' or unit_val == 'ml':
             final_qty = int(qty_raw)
        else:
             final_qty = int(qty_raw)

        database.update_inventory_item(item_id, name=name, quantity=final_qty, unit=final_unit, expiry_date=expiry, buy_date=buy, area=area)
        self.edit_dialog.dismiss()
        self.load_data()

    def on_item_selected(self, item_id, is_active):
        if is_active:
            self.selected_items.add(item_id)
        else:
            self.selected_items.discard(item_id)
        self.update_batch_delete_btn()

    def update_batch_delete_btn(self):
        count = len(self.selected_items)
        if count > 0:
            self.batch_delete_btn.text = f"批量刪除 ({count})"
            self.batch_delete_btn.opacity = 1
            self.batch_delete_btn.disabled = False
        else:
            self.batch_delete_btn.opacity = 0
            self.batch_delete_btn.disabled = True

    def confirm_bulk_delete(self, *args):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.bulk_delete_dialog = MDDialog(
            title="確認批量刪除",
            type="custom",
            content_cls=MDLabel(text=f"確定要刪除選中的 {len(self.selected_items)} 個項目嗎？", font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["close"], font_name='chinese_font', on_release=lambda x: self.bulk_delete_dialog.dismiss()),
                MDFlatButton(text=d["ok"], font_name='chinese_font', theme_text_color="Custom", text_color=[0.8, 0.2, 0.2, 1], 
                             on_release=self.execute_bulk_delete)
            ],
        )
        self.bulk_delete_dialog.open()

    def execute_bulk_delete(self, *args):
        for item_id in self.selected_items:
            database.delete_inventory_item(item_id)
        
        self.bulk_delete_dialog.dismiss()
        self.selected_items.clear()
        self.load_data()
        
        from kivymd.toast import toast
        toast("已成功刪除選中項目")

    def confirm_delete(self, item_id):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        from kivymd.uix.button import MDFlatButton
        self.delete_dialog = MDDialog(
            title=d.get("delete_confirm", "Confirm Delete"),
            type="custom",
            content_cls=MDLabel(text=d.get("delete_item_msg", "Are you sure you want to delete this item?"), font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["close"], font_name='chinese_font', on_release=lambda x: self.delete_dialog.dismiss()),
                MDFlatButton(text=d["ok"], font_name='chinese_font', theme_text_color="Custom", text_color=[0.8, 0.2, 0.2, 1], 
                             on_release=lambda x: self.execute_delete(item_id))
            ],
        )
        self.delete_dialog.open()

    def execute_delete(self, item_id):
        database.delete_inventory_item(item_id)
        if hasattr(self, 'delete_dialog'):
            self.delete_dialog.dismiss()
        self.load_data()

    def open_menu(self, button):
        if not self.menu:
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            menu_items = [
                {
                    "text": d.get("manual_entry", "Manual Entry"),
                    "viewclass": "OneLineListItem",
                    "on_release": lambda: self.menu_callback("manual"),
                    "font_name": "chinese_font",
                },
                {
                    "text": d.get("camera_entry", "AI Recognition"),
                    "viewclass": "OneLineListItem",
                    "on_release": lambda: self.menu_callback("camera"),
                    "font_name": "chinese_font",
                }
            ]
            self.menu = MDDropdownMenu(
                caller=button,
                items=menu_items,
                width_mult=4,
            )
        self.menu.open()

    def menu_callback(self, action):
        self.menu.dismiss()
        if action == "manual":
            self.show_add_dialog()
        elif action == "camera":
            self.open_camera()

    def open_camera(self, *args):
        try:
            from plyer import filechooser
            filechooser.open_file(
                title=LANG_DICT[MDApp.get_running_app().current_lang]["select_photo"],
                filters=[("Images", "*.jpg", "*.png", "*.jpeg")],
                on_selection=self.process_selected_image
            )
        except Exception as e:
            print(f"Filechooser error: {e}")
            
    def process_selected_image(self, selection):
        if not selection: return
        image_path = selection[0]
        self.recognize_and_add(image_path)
        
    def recognize_and_add(self, image_path):
        from kivymd.toast import toast
        toast(LANG_DICT[MDApp.get_running_app().current_lang]["ai_recognizing"])
        
        # Use async method
        ai_manager.recognize_food_from_image_async(self.on_recognize_complete, image_path)
            
    def on_recognize_complete(self, data):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        from kivymd.toast import toast
        
        if data:
            name = data.get("name", d["unknown"])
            qty_raw = data.get("quantity", 1)
            
            # Parse Unit
            final_qty = 1
            final_unit = "unit"
            
            import re
            match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)?", str(qty_raw))
            if match:
                try:
                    q_val = float(match.group(1))
                    u_val = match.group(2)
                    
                    if u_val:
                        u_val = u_val.lower()
                        if u_val in ['kg', 'kilogram']:
                            final_qty = int(q_val * 1000)
                            final_unit = 'g'
                        elif u_val in ['l', 'liter']:
                            final_qty = int(q_val * 1000)
                            final_unit = 'ml'
                        elif u_val in ['g', 'gram']:
                            final_qty = int(q_val)
                            final_unit = 'g'
                        elif u_val in ['ml']:
                            final_qty = int(q_val)
                            final_unit = 'ml'
                        else:
                            final_qty = int(q_val)
                            final_unit = 'unit'
                    else:
                        final_qty = int(q_val)
                        final_unit = 'unit'
                except:
                    final_qty = 1
            
            # Fix NameError
            buy_date = datetime.now().strftime("%Y-%m-%d")
            expiry_date = "" 
            
            # AI Category
            area = ai_manager.estimate_item_category(name)
            
            database.add_inventory_item(name, final_qty, final_unit, expiry_date, buy_date, area)
            self.load_data()
            
            toast(d["auto_added"].format(name=name) + f" ({area})")
        else:
            toast(d["recog_failed"])

    def show_add_dialog(self, instance=None):
        if not hasattr(self, 'dialog') or not self.dialog: 
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            self.name_field = MDTextField(hint_text=d["item_name"], font_name='chinese_font', font_name_hint_text='chinese_font')
            # Quantity is number only
            self.qty_field = MDTextField(hint_text=d["quantity"], input_filter="float", font_name='chinese_font', font_name_hint_text='chinese_font')
            
            # Unit Type Selector
            self.unit_type_field = MDTextField(
                text=d["u_qty"], # Localizedized Default
                hint_text=d["u_type"],
                font_name='chinese_font',
                font_name_hint_text='chinese_font',
                readonly=True
            )
            self.unit_type_field.bind(focus=self.on_unit_type_focus)
            
            # Unit Selector
            self.unit_field = MDTextField(
                text=d["unit_pc"], # Localized Default
                hint_text=d["u_unit"],
                font_name='chinese_font',
                font_name_hint_text='chinese_font',
                readonly=True
            )
            self.unit_field.bind(focus=self.on_unit_focus)
            
            self.expiry_date_field = MDTextField(hint_text=d["expiry_date"], font_name='chinese_font', font_name_hint_text='chinese_font')
            
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            self.buy_date_field = MDTextField(text=today, hint_text=d["buy_date"], font_name='chinese_font', font_name_hint_text='chinese_font')
            
            # Area Selector Field (Read-only TextField acting as dropdown trigger)
            self.area_field = MDTextField(
                text=d[self.current_category],
                hint_text=d["area"],
                font_name='chinese_font',
                font_name_hint_text='chinese_font',
                readonly=True,
                # halign="left" is default, removed center
            )
            # Bind focus to open menu
            self.area_field.bind(focus=self.on_area_field_focus)
            
            # -- Menus --
            
            # Unit Types (Localized)
            self.unit_type_menu = MDDropdownMenu(
                caller=self.unit_type_field,
                items=[
                    {"text": d["u_weight"], "viewclass": "OneLineListItem", "on_release": lambda: self.set_unit_type(d["u_weight"])},
                    {"text": d["u_volume"], "viewclass": "OneLineListItem", "on_release": lambda: self.set_unit_type(d["u_volume"])},
                    {"text": d["u_qty"], "viewclass": "OneLineListItem", "on_release": lambda: self.set_unit_type(d["u_qty"])},
                ],
                width_mult=4,
            )
            
            # Units (Dynamic)
            self.update_unit_menu("Quantity") # Init with internal key
            
            # Area Menu
            menu_items = []
            for cat_key in self.categories:
                 menu_items.append({
                     "text": d[cat_key],
                     "viewclass": "OneLineListItem",
                     "on_release": lambda x=d[cat_key]: self.set_area_text(x),
                     "font_name": "chinese_font"
                 })
            
            self.area_menu = MDDropdownMenu(
                caller=self.area_field,
                items=menu_items,
                width_mult=4,
            )
            
            # Layout for Quantity + Units
            qty_layout = MDBoxLayout(orientation='horizontal', spacing="10dp")
            qty_layout.add_widget(self.qty_field)
            qty_layout.add_widget(self.unit_type_field)
            qty_layout.add_widget(self.unit_field)

            self.dialog = MDDialog(
                title=d["add_item"],
                type="custom",
                content_cls=MDBoxLayout(
                    self.name_field,
                    qty_layout,
                    self.expiry_date_field,
                    self.buy_date_field,
                    self.area_field,
                    orientation="vertical",
                    spacing="12dp",
                    size_hint_y=None,
                    height="480dp" # Increased height
                ),
                buttons=[
                    MDFillRoundFlatButton(text=d["cancel"], font_name='chinese_font', on_release=self.close_dialog),
                    MDFillRoundFlatButton(text=d["save"], font_name='chinese_font', on_release=self.save_item),
                ],
            )
        self.dialog.open()
        
    def on_unit_type_focus(self, instance, focused):
        if focused: self.unit_type_menu.open()

    def on_unit_focus(self, instance, focused):
        if focused: self.unit_menu.open()

    def set_unit_type(self, localized_type_name):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Map localized text back to internal logic keys
        reverse_type_map = {
            d["u_weight"]: "Weight",
            d["u_volume"]: "Volume",
            d["u_qty"]: "Quantity"
        }
        
        internal_type = reverse_type_map.get(localized_type_name, "Quantity")
        self.unit_type_field.text = localized_type_name
        self.unit_type_menu.dismiss()
        self.unit_type_field.focus = False
        self.update_unit_menu(internal_type)
        
    def update_unit_menu(self, type_name):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        unit_label_map = {
            "g": d["unit_g"],
            "kg": d["unit_kg"],
            "ml": d["unit_ml"],
            "l": d["unit_l"],
            "unit": d["unit_pc"]
        }
        
        units = []
        if type_name == "Weight":
            units = ["g", "kg"]
            self.unit_field.text = d["unit_g"]
        elif type_name == "Volume":
            units = ["ml", "l"]
            self.unit_field.text = d["unit_ml"]
        else:
            units = ["unit"]
            self.unit_field.text = d["unit_pc"]
            
        items = []
        for u in units:
            label = unit_label_map.get(u, u)
            items.append({
                "text": label,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=label: self.set_unit(x)
            })
            
        self.unit_menu = MDDropdownMenu(
            caller=self.unit_field,
            items=items,
            width_mult=2,
        )

    def set_unit(self, unit_name):
        self.unit_field.text = unit_name
        self.unit_menu.dismiss()
        self.unit_field.focus = False

    def on_area_field_focus(self, instance, focused):
        if focused:
            self.area_menu.open()
            
    def open_area_menu(self, *args):
        self.area_menu.open()
        
    def set_area_text(self, text_item):
        self.area_field.text = text_item
        self.area_menu.dismiss()
        self.area_field.focus = False # Remove focus so it can be clicked again
        
    def close_dialog(self, *args):
        self.dialog.dismiss()

    def save_item(self, *args):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        name = self.name_field.text
        if not name: return
        
        try:
            qty_raw = float(self.qty_field.text) if self.qty_field.text else 1.0
            
            # Map localized unit back to internal database code
            reverse_unit_map = {
                d["unit_g"]: "g",
                d["unit_kg"]: "kg",
                d["unit_ml"]: "ml",
                d["unit_l"]: "l",
                d["unit_pc"]: "unit"
            }
            unit_val = reverse_unit_map.get(self.unit_field.text, "unit")
            
            # Normalization
            final_qty = int(qty_raw)
            final_unit = unit_val
            
            if unit_val == 'kg':
                 final_qty = int(qty_raw * 1000)
                 final_unit = 'g'
            elif unit_val == 'l':
                 final_qty = int(qty_raw * 1000)
                 final_unit = 'ml'
            elif unit_val == 'g' or unit_val == 'ml':
                 final_qty = int(qty_raw)
            else:
                 final_qty = int(qty_raw)

            expiry_date = self.expiry_date_field.text
            buy_date = self.buy_date_field.text
            area = self.area_field.text if self.area_field.text else "General"
            
            database.add_inventory_item(name, final_qty, final_unit, expiry_date, buy_date, area)
            self.load_data()
            self.close_dialog()
            
            self.name_field.text = ""
            self.qty_field.text = ""
            self.expiry_date_field.text = ""
            self.buy_date_field.text = ""
            self.area_field.text = ""
            
        except ValueError:
            print("Invalid Input")

    def show_shopping_dialog(self, *args):
        # Import internally to avoid circular imports if any, though screens usually safe
        from ui.screens.shopping import ShoppingListContent
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Create Content Instance
        content = ShoppingListContent()
        
        # Wrap content in a layout that constrains height? 
        # MDDialog type="custom" usually handles content size if hint_y is not None
        # ShoppingListContent has scrollview so it should expand.
        # We need to ensure it has a size.
        content.size_hint_y = None
        content.height = dp(500) # Fixed height for dialog
        
        self.shop_dialog = MDDialog(
            title=d.get("shopping_list", "Shopping List"),
            type="custom",
            content_cls=content,
            buttons=[
                MDFillRoundFlatButton(
                    text=d["close"], 
                    font_name='chinese_font',
                    on_release=lambda x: self.shop_dialog.dismiss()
                )
            ]
        )
        self.shop_dialog.open()


