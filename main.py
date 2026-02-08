from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.list import TwoLineAvatarIconListItem
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp

import database
import calories
import ui.screens
import ui.login
from ui.localization import LANG_DICT
import os
from dotenv import load_dotenv

load_dotenv()

def setup_chinese_font():
    font_path = r'C:\Windows\Fonts\msjh.ttc'
    # 註冊字體別名
    try:
        LabelBase.register(name='chinese_font', fn_regular=font_path)
    except Exception as e:
        print(f"Error loading font: {e}")


# Set Window size to mimic mobile for testing on PC
Window.size = (400, 750)

class MainApp(MDApp):
    def build(self):
        # Setup Chinese font support
        setup_chinese_font()
        
        # Ensure database tables exist before doing anything else
        database.init_db()
        
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Gray"
        self.theme_cls.theme_style = "Light"
        
        # Force use Chinese font for all text styles, but exclude 'Icon' to keep system icons working
        for style in self.theme_cls.font_styles:
            if style != "Icon":
                self.theme_cls.font_styles[style][0] = "chinese_font"
        
        self.current_lang = "zh"
        
        # Main Layout: Bottom Nav
        self.screen_manager = MDScreenManager()
        
        self.nav = MDBottomNavigation()
        self.update_nav_colors()
        
        # Screen 1: Family
        self.screen_family = MDBottomNavigationItem(
            name="screen_family",
            text=LANG_DICT[self.current_lang]["family"],
            icon="account-group",
        )
        self.family_view = ui.screens.FamilyScreen()
        self.screen_family.add_widget(self.family_view)
        
        # Screen 2: Inventory
        self.screen_inv = MDBottomNavigationItem(
            name="screen_inv",
            text=LANG_DICT[self.current_lang]["inventory"],
            icon="fridge",
        )
        self.inventory_view = ui.screens.InventoryScreen()
        self.screen_inv.add_widget(self.inventory_view)

        # Screen 3: Calories
        self.screen_cal = MDBottomNavigationItem(
            name="screen_cal",
            text=LANG_DICT[self.current_lang]["calories"],
            icon="fire",
        )
        self.calories_db = calories.DatabaseManager()
        # Initialize dummy data if empty
        if self.calories_db.get_today_total() == 0:
             self.calories_db.add_record('breakfast', 400) # dummy

        self.calories_view = calories.MainInterface(self.calories_db)
        self.screen_cal.add_widget(self.calories_view)
        
        # Screen 4: AI Chat
        self.screen_ai = MDBottomNavigationItem(
            name="screen_ai",
            text=LANG_DICT[self.current_lang]["chat"],
            icon="robot",
        )
        
        self.ai_layout = ui.screens.AIChatScreen()
        self.screen_ai.add_widget(self.ai_layout)
        
        self.nav.add_widget(self.screen_family)
        self.nav.add_widget(self.screen_inv)
        self.nav.add_widget(self.screen_cal)
        self.nav.add_widget(self.screen_ai)
        
        # Wrap nav in MainScreen
        self.main_screen = ui.screens.MainScreen(name="main")
        self.main_screen.add_widget(self.nav)
        
        # Combine everything in ScreenManager
        self.splash_screen = ui.screens.SplashScreen(name="splash")
        self.login_screen = ui.login.LoginScreen(name="login")
        self.screen_manager.add_widget(self.splash_screen)
        self.screen_manager.add_widget(self.login_screen)
        self.screen_manager.add_widget(self.main_screen)
        
        return self.screen_manager

    def update_nav_colors(self):
        is_dark = self.theme_cls.theme_style == "Dark"
        bg_col = [0.1, 0.1, 0.1, 1] if is_dark else [1, 1, 1, 1]
        text_col = [1, 1, 1, 1] if is_dark else [0.4, 0.4, 0.4, 1]
        active_col = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        
        self.nav.panel_color = bg_col
        self.nav.text_color_normal = text_col
        self.nav.text_color_active = active_col

    def open_settings(self):
        d = LANG_DICT[self.current_lang]
        self.settings_dialog = MDDialog(
            title=d["settings"],
            type="simple",
            items=[
                TwoLineAvatarIconListItem(
                    text=d["lang"], 
                    secondary_text=d[self.current_lang],
                    on_release=self.show_lang_options
                ),
                TwoLineAvatarIconListItem(
                    text=d["theme"], 
                    secondary_text=d["dark"] if self.theme_cls.theme_style == "Dark" else d["light"],
                    on_release=self.show_theme_options
                ),
                TwoLineAvatarIconListItem(
                    text=d["logout"], 
                    secondary_text="",
                    on_release=self.confirm_logout
                ),
            ],
        )
        self.settings_dialog.open()
    
    def confirm_logout(self, *args):
        self.settings_dialog.dismiss()
        d = LANG_DICT[self.current_lang]
        self.logout_dialog = MDDialog(
            title=d["logout"],
            text=d["confirm_logout_msg"],
            buttons=[
                MDFillRoundFlatButton(text=d["cancel"], on_release=lambda x: self.logout_dialog.dismiss()),
                MDFillRoundFlatButton(
                    text=d["logout"], 
                    md_bg_color=(0.8, 0, 0, 1),
                    on_release=self.logout_action
                ),
            ],
        )
        self.logout_dialog.open()

    def logout_action(self, *args):
        database.logout()
        if hasattr(self, 'logout_dialog'):
            self.logout_dialog.dismiss()
        
        # Reset UI if needed
        self.current_lang = "zh" # Optional: reset or keep language preference
        self.refresh_ui_text()
        
        from kivymd.uix.transition import MDFadeSlideTransition
        self.screen_manager.transition = MDFadeSlideTransition(duration=0.5)
        self.screen_manager.current = "login"
    
    def show_ai_settings(self, *args):
        self.settings_dialog.dismiss()
        d = LANG_DICT[self.current_lang]
        
        current_key = database.get_setting("gemini_api_key") or ""
        self.api_key_field = MDTextField(
            text=current_key,
            hint_text=d["api_key"],
            helper_text=d["enter_key"],
            helper_text_mode="on_focus"
        )
        
        self.ai_dialog = MDDialog(
            title=d["ai_settings"],
            type="custom",
            content_cls=MDBoxLayout(
                self.api_key_field,
                orientation="vertical",
                size_hint_y=None,
                height=dp(80)
            ),
            buttons=[
                MDFillRoundFlatButton(text=d["cancel"], on_release=lambda x: self.ai_dialog.dismiss()),
                MDFillRoundFlatButton(text=d["save"], on_release=self.save_api_key),
            ],
        )
        self.ai_dialog.open()

    def save_api_key(self, *args):
        new_key = self.api_key_field.text.strip()
        database.set_setting("gemini_api_key", new_key)
        self.ai_dialog.dismiss()
        from kivymd.uix.snackbar import Snackbar
        d = LANG_DICT[self.current_lang]
        Snackbar(text=d["key_saved"]).open()

    def show_lang_options(self, *args):
        self.settings_dialog.dismiss()
        d = LANG_DICT[self.current_lang]
        self.lang_dialog = MDDialog(
            title=d["lang"],
            type="simple",
            items=[
                TwoLineAvatarIconListItem(text=d["zh"], on_release=lambda x: self.change_lang("zh")),
                TwoLineAvatarIconListItem(text=d["en"], on_release=lambda x: self.change_lang("en")),
            ],
        )
        self.lang_dialog.open()

    def change_lang(self, lang_code):
        self.current_lang = "en" if lang_code == "en" else "zh"
        self.lang_dialog.dismiss()
        self.refresh_ui_text()

    def show_theme_options(self, *args):
        self.settings_dialog.dismiss()
        d = LANG_DICT[self.current_lang]
        self.theme_dialog = MDDialog(
            title=d["theme"],
            type="simple",
            items=[
                TwoLineAvatarIconListItem(
                    text=d["light"], 
                    on_release=lambda x: self.change_theme("Light")
                ),
                TwoLineAvatarIconListItem(
                    text=d["dark"], 
                    on_release=lambda x: self.change_theme("Dark")
                ),
            ],
        )
        self.theme_dialog.open()

    def change_theme(self, theme_style):
        self.theme_cls.theme_style = theme_style
        if hasattr(self, 'theme_dialog'):
            self.theme_dialog.dismiss()
        self.update_all_colors()

    def update_all_colors(self):
        self.update_nav_colors()
        
        # Profile View
        self.family_view.update_theme_colors()
        self.family_view.load_data() # Refresh cards
        
        # Inventory View
        self.inventory_view.update_theme_colors()
        self.inventory_view.load_data()
        
        # AI Chat View
        self.ai_layout.update_theme_colors()

        # Calories View
        if hasattr(self, 'calories_view'):
            self.calories_view.update_theme_colors()
            self.calories_view.refresh_ui()
        
        # Update existing dialogs instead of just setting to None
        if hasattr(self.family_view, 'dialog') and self.family_view.dialog:
            if hasattr(self.family_view.dialog, 'update_theme_colors'):
                self.family_view.dialog.update_theme_colors()
            else:
                self.family_view.dialog = None # Fallback
                
        if hasattr(self.inventory_view, 'dialog') and self.inventory_view.dialog:
            self.inventory_view.dialog = None 

    def refresh_ui_text(self):
        d = LANG_DICT[self.current_lang]
        
        # Update Navigation Tabs
        self.screen_family.text = d["family"]
        self.screen_inv.text = d["inventory"]
        self.screen_cal.text = d["calories"]
        self.screen_ai.text = d["chat"]
        
        # Update Toolbars
        self.family_view.toolbar.title = d["family"]
        self.inventory_view.toolbar.title = d["inventory"]
        self.ai_layout.ai_toolbar.title = d["chat"]
        
        # Update Specific Search/Input hints
        self.ai_layout.chat_input.hint_text = d["ask_ai"]
        
        # Refresh Screen Contents (Empty labels etc.)
        self.family_view.load_data()
        self.inventory_view.load_data()
        if hasattr(self, 'calories_view'):
            self.calories_view.toolbar.title = d["calories"]
            self.calories_view.refresh_ui()
        
        # Re-initialize dialogs on next open to use new language
        self.family_view.dialog = None
        self.inventory_view.dialog = None
        
        # Update colors (just in case)
        self.update_all_colors()

    def switch_to_chat(self):
        self.nav.switch_tab("screen_ai")

if __name__ == "__main__":
    app = MainApp()
    app.run()
