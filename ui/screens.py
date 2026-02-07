from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDIconButton, MDFloatingActionButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.spinner import MDSpinner
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout

import database
import ai_manager
from ui.localization import LANG_DICT
from ui.cards import FamilyCard
from ui.dialogs import AddMemberSheet
import os

class SplashScreen(MDScreen):
    def on_enter(self, *args):
        # Initial state: only loader visible and active
        self.ids.loader.active = True
        self.ids.loader.opacity = 0
        
        # Fade in loader
        Animation(opacity=1, duration=1.0).start(self.ids.loader)
        
        # Wait 5 seconds then go to main
        Clock.schedule_once(self.to_main, 5.0)
        
    def to_main(self, *args):
        app = MDApp.get_running_app()
        from kivymd.uix.transition import MDFadeSlideTransition
        app.screen_manager.transition = MDFadeSlideTransition(duration=0.5)
        app.screen_manager.current = "login"

Builder.load_string('''
<SplashScreen>:
    md_bg_color: app.theme_cls.bg_normal
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        MDSpinner:
            id: loader
            size_hint: None, None
            size: dp(40), dp(40)
            pos_hint: {'center_x': .5}
            active: False
            opacity: 0
''')

class MainScreen(MDScreen):
    pass

class FamilyScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_theme_colors()
        self.layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        # ScrollView for Family Cards
        self.scroll = MDScrollView()
        self.card_list = MDBoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20), size_hint_y=None)
        self.card_list.bind(minimum_height=self.card_list.setter('height'))
        
        self.scroll.add_widget(self.card_list)
        self.layout.add_widget(self.scroll)
        
        # FAB for Adding Member
        self.overlay = FloatLayout()
        fab = MDFloatingActionButton(
            icon="plus",
            type="standard",
            md_bg_color=[0.6, 0.6, 0.6, 1],
            elevation=0,
            pos_hint={"right": 0.95, "y": 0.1}
        )
        fab.bind(on_release=self.show_add_dialog)
        self.overlay.add_widget(fab)
        
        self.main_float = MDBoxLayout(orientation='vertical')
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.toolbar = MDTopAppBar(
            title=d["family"], 
            elevation=0,
            left_action_items=[["cog", lambda x: MDApp.get_running_app().open_settings()]]
        )
        self.toolbar.right_action_items = [["message-text-outline", lambda x: app.switch_to_chat()]]
        self.update_theme_colors()
        
        self.main_float.add_widget(self.toolbar)
        self.main_float.add_widget(self.layout)
        
        self.add_widget(self.main_float)
        self.add_widget(self.overlay)
        self.dialog = None
        self.load_data()

    def update_theme_colors(self, *args):
        is_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        self.md_bg_color = [0.07, 0.07, 0.07, 1] if is_dark else [0.95, 0.95, 0.95, 1]
        if hasattr(self, 'toolbar'):
            self.toolbar.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else [1, 1, 1, 1]
            self.toolbar.specific_text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]

    def load_data(self):
        self.card_list.clear_widgets()
        members = database.get_family_members()
        
        if not members:
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            empty_lbl = MDLabel(
                text=d["no_members"],
                halign="center",
                theme_text_color="Hint"
            )
            self.card_list.add_widget(empty_lbl)
        
        for m in members:
            card = FamilyCard(member_data=m, delete_callback=self.confirm_delete_member)
            self.card_list.add_widget(card)

    def confirm_delete_member(self, member_id, name):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.confirm_dialog = MDDialog(
            title=d["delete_confirm"],
            text=d["delete_msg"].format(name=name),
            buttons=[
                MDFillRoundFlatButton(
                    text=d["cancel"],
                    on_release=lambda x: self.confirm_dialog.dismiss()
                ),
                MDFillRoundFlatButton(
                    text=d["delete_confirm"].split()[-1],
                    md_bg_color=(0.8, 0, 0, 1),
                    on_release=lambda x: self.delete_member_now(member_id)
                ),
            ],
        )
        self.confirm_dialog.open()

    def delete_member_now(self, member_id):
        try:
            database.delete_family_member(member_id)
            if self.confirm_dialog:
                self.confirm_dialog.dismiss()
            self.load_data()
        except Exception as e:
            print(f"Error deleting member: {e}")

    def show_add_dialog(self, instance):
        if not self.dialog:
            self.dialog = AddMemberSheet(save_callback=self.save_member_data)
        self.dialog.open()

    def save_member_data(self, name, age, sex, allergens, genetic, height, weight):
        try:
            database.add_family_member(name, age, sex, allergens, genetic, height, weight)
            self.load_data()
            self.dialog = None 
        except Exception as e:
            print(f"Error saving: {e}")

class InventoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        self.scroll = MDScrollView()
        self.list_layout = MDList()
        self.scroll.add_widget(self.list_layout)
        
        self.layout.add_widget(self.scroll)
        
        self.main_float = MDBoxLayout(orientation='vertical')
        
        self.overlay = FloatLayout()
        
        # Camera FAB (Centered)
        self.cam_fab = MDFloatingActionButton(
            icon="camera",
            type="standard",
            md_bg_color=[0.6, 0.6, 0.6, 1],
            elevation=0,
            pos_hint={"center_x": 0.5, "y": 0.1}
        )
        self.cam_fab.bind(on_release=self.open_camera)
        
        # Plus FAB (Right side)
        self.fab = MDFloatingActionButton(
            icon="plus",
            type="standard",
            md_bg_color=[0.6, 0.6, 0.6, 1],
            elevation=0,
            pos_hint={"right": 0.95, "y": 0.1}
        )
        self.fab.bind(on_release=self.show_add_dialog)
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.toolbar = MDTopAppBar(
            title=d["inventory"], 
            elevation=0,
            left_action_items=[["cog", lambda x: MDApp.get_running_app().open_settings()]]
        )
        self.toolbar.right_action_items = [["message-text-outline", lambda x: app.switch_to_chat()]]
        
        self.main_float.add_widget(self.toolbar)
        self.main_float.add_widget(self.layout)
        
        self.overlay.add_widget(self.cam_fab)
        self.overlay.add_widget(self.fab)
        self.add_widget(self.main_float)
        self.add_widget(self.overlay)
        
        self.update_theme_colors()
        self.load_data()
        
    def update_theme_colors(self, *args):
        is_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        bg_color = [0.07, 0.07, 0.07, 1] if is_dark else [0.95, 0.95, 0.95, 1]
        self.md_bg_color = bg_color
        if hasattr(self, 'main_float'):
            self.main_float.md_bg_color = bg_color
            
        if hasattr(self, 'toolbar'):
            self.toolbar.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else [1, 1, 1, 1]
            self.toolbar.specific_text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]
            
        if hasattr(self, 'fab'):
            self.fab.md_bg_color = [0.6, 0.6, 0.6, 1]
        if hasattr(self, 'cam_fab'):
            self.cam_fab.md_bg_color = [0.6, 0.6, 0.6, 1]

    def load_data(self):
        self.list_layout.clear_widgets()
        items = database.get_all_inventory()
        
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        d = LANG_DICT[app.current_lang]
        
        text_color = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        secondary_color = [0.9, 0.9, 0.9, 1] if is_dark else [0.6, 0.6, 0.6, 1]
        
        if not items:
            self.list_layout.add_widget(
                MDLabel(
                    text=d["no_items"], 
                    halign="center", 
                    theme_text_color="Custom", 
                    text_color=text_color,
                    font_name='chinese_font'
                )
            )
            return

        for item in items:
            item_id, name, qty, expiry_date, buy_date, area = item
            
            text = f"{name} (x{qty})"
            secondary = f"Exp: {expiry_date} | Area: {area}"
            
            li = TwoLineAvatarIconListItem(
                text=text, 
                secondary_text=secondary,
                theme_text_color="Custom",
                text_color=text_color,
                secondary_theme_text_color="Custom",
                secondary_text_color=secondary_color
            )
            li.add_widget(IconLeftWidget(
                icon="food-variant",
                theme_text_color="Custom",
                icon_color=text_color
            )) 
            
            li.add_widget(IconRightWidget(
                icon="delete-outline",
                theme_text_color="Custom",
                icon_color=secondary_color,
                on_release=lambda x, i=item_id: self.confirm_delete(i)
            ))
            
            self.list_layout.add_widget(li)

    def confirm_delete(self, item_id):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        from kivymd.uix.button import MDFlatButton
        self.delete_dialog = MDDialog(
            title=d.get("delete_confirm", "Confirm Delete"),
            text=d.get("delete_item_msg", "Are you sure you want to delete this item?"),
            buttons=[
                MDFlatButton(text=d["close"], on_release=lambda x: self.delete_dialog.dismiss()),
                MDFlatButton(text="OK", theme_text_color="Custom", text_color=[0.8, 0.2, 0.2, 1], 
                             on_release=lambda x: self.execute_delete(item_id))
            ],
        )
        self.delete_dialog.open()

    def execute_delete(self, item_id):
        database.delete_inventory_item(item_id)
        if hasattr(self, 'delete_dialog'):
            self.delete_dialog.dismiss()
        self.load_data()

    def open_camera(self, *args):
        try:
            from plyer import filechooser
            filechooser.open_file(
                title="Select Food Photo",
                filters=[("Images", "*.jpg", "*.png", "*.jpeg")],
                on_selection=self.process_selected_image
            )
        except Exception as e:
            print(f"Filechooser error: {e}")
            
    def process_selected_image(self, selection):
        if not selection: return
        image_path = selection[0]
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=d["ai_recognizing"]).open()
        
        Clock.schedule_once(lambda dt: self.recognize_and_add(image_path), 0.5)
        
    def recognize_and_add(self, image_path):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        from kivymd.uix.snackbar import Snackbar
        
        api_key = os.getenv("GEMINI_API_KEY") or database.get_setting("gemini_api_key")
        if not api_key:
            Snackbar(text=d["key_missing_msg"], font_name='chinese_font').open()
            return

        data = ai_manager.recognize_food_from_image(image_path)
        
        if data:
            name = data.get("name", "Unknown")
            qty = data.get("quantity", 1)
            expiry_days = data.get("expiry_days", 7)
            area = data.get("area", "General")
            
            from datetime import datetime, timedelta
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
            buy_date = datetime.now().strftime("%Y-%m-%d")
            
            database.add_inventory_item(name, qty, expiry_date, buy_date, area)
            self.load_data()
            
            Snackbar(text=d["auto_added"].format(name=name), font_name='chinese_font').open()
        else:
            Snackbar(text="Recognition failed. Please try again.").open()

    def show_add_dialog(self, instance):
        if not hasattr(self, 'dialog') or not self.dialog: 
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            self.name_field = MDTextField(hint_text=d["item_name"], font_name='chinese_font', font_name_hint_text='chinese_font')
            self.qty_field = MDTextField(hint_text=d["quantity"], input_filter="int", font_name='chinese_font', font_name_hint_text='chinese_font')
            self.expiry_date_field = MDTextField(hint_text=d["expiry_date"], font_name='chinese_font', font_name_hint_text='chinese_font')
            self.buy_date_field = MDTextField(hint_text=d["buy_date"], font_name='chinese_font', font_name_hint_text='chinese_font')
            self.area_field = MDTextField(hint_text=d["area"], font_name='chinese_font', font_name_hint_text='chinese_font')
            
            self.dialog = MDDialog(
                title=d["add_item"],
                type="custom",
                content_cls=MDBoxLayout(
                    self.name_field,
                    self.qty_field,
                    self.expiry_date_field,
                    self.buy_date_field,
                    self.area_field,
                    orientation="vertical",
                    spacing="12dp",
                    size_hint_y=None,
                    height="400dp"
                ),
                buttons=[
                    MDFillRoundFlatButton(text=d["cancel"], on_release=self.close_dialog),
                    MDFillRoundFlatButton(text=d["save"], on_release=self.save_item),
                ],
            )
        self.dialog.open()

    def close_dialog(self, *args):
        self.dialog.dismiss()

    def save_item(self, *args):
        name = self.name_field.text
        if not name: return
        
        try:
            qty = int(self.qty_field.text) if self.qty_field.text else 1
            expiry_date = self.expiry_date_field.text
            buy_date = self.buy_date_field.text
            area = self.area_field.text if self.area_field.text else "General"
            
            database.add_inventory_item(name, qty, expiry_date, buy_date, area)
            self.load_data()
            self.close_dialog()
            
            self.name_field.text = ""
            self.qty_field.text = ""
            self.expiry_date_field.text = ""
            self.buy_date_field.text = ""
            self.area_field.text = ""
            
        except ValueError:
            print("Invalid Input")

class AIChatScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.orientation = 'vertical'
        
        # Chat History
        self.chat_scroll = MDScrollView()
        self.chat_list = MDList()
        self.chat_scroll.add_widget(self.chat_list)
        
        # Input Area
        input_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=dp(5), spacing=dp(5))
        self.chat_input = MDTextField(hint_text=d["ask_ai"], mode="fill", font_name='chinese_font', font_name_hint_text='chinese_font')
        send_btn = MDIconButton(icon="send", on_release=self.send_ai_message)
        
        input_box.add_widget(self.chat_input)
        input_box.add_widget(send_btn)
        
        self.ai_toolbar = MDTopAppBar(
            title=d["chat"], 
            elevation=0,
            anchor_title="center",
            left_action_items=[["cog", lambda x: MDApp.get_running_app().open_settings()]]
        )
        self.add_widget(self.ai_toolbar)
        self.add_widget(self.chat_scroll)
        self.add_widget(input_box)
        self.update_theme_colors()

    def update_theme_colors(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        self.md_bg_color = [0.07, 0.07, 0.07, 1] if is_dark else [0.95, 0.95, 0.95, 1]
        self.ai_toolbar.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else [1, 1, 1, 1]
        self.ai_toolbar.specific_text_color = [0.9, 0.9, 0.9, 1] if is_dark else [0.2, 0.2, 0.2, 1]

    def send_ai_message(self, instance):
        msg = self.chat_input.text
        if not msg: return
        
        # User Message
        self.chat_list.add_widget(TwoLineAvatarIconListItem(
            text="You", 
            secondary_text=msg, 
            bg_color=(0.9, 0.9, 0.9, 1)
        ))
        
        self.chat_input.text = ""
        
        d = LANG_DICT[MDApp.get_running_app().current_lang]
        self.chat_list.add_widget(MDLabel(text=d["ai_thinking"], theme_text_color="Secondary", size_hint_y=None, height=dp(30), font_name='chinese_font'))
        
        Clock.schedule_once(lambda dt: self.get_ai_response(msg), 0.1)

    def get_ai_response(self, msg):
        if self.chat_list.children:
             self.chat_list.remove_widget(self.chat_list.children[0])
        
        try:
            family_data = database.get_family_members()
            inventory_data = database.get_all_inventory()
            
            response = ai_manager.get_ai_chat_response(msg, family_data, inventory_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            response = f"System Error: {str(e)}"
        
        self.chat_list.add_widget(TwoLineAvatarIconListItem(
            text="AI Assistant", 
            secondary_text=response[:100] + "..." if len(response) > 100 else response,
            on_release=lambda x: self.show_full_response(response)
        ))
        
    def show_full_response(self, text):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        dialog = MDDialog(
            title=d["ai_recommendation"],
            text=text,
            buttons=[MDFillRoundFlatButton(text=d["close"], on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
