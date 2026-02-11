from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton, MDTextButton
from kivymd.uix.label import MDLabel
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.fitimage import FitImage
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
import database
from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_ACCENT_SAGE, COLOR_TEXT_DARK_GREY
import os

# Get the base directory for assets relative to this file
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'TATA'))

# Colors from the design
COLOR_LOGIN_BTN = get_color_from_hex("#FCDD6D") # Yellow/Gold
COLOR_LOGIN_BTN_TEXT = get_color_from_hex("#5D4037") # Dark Brown
COLOR_CARD_BG = [1, 1, 1, 0.85] # Translucent White

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        
        # 1. Background Image
        bg_image_path = os.path.join(ASSETS_DIR, 'log.png') 
        self.add_widget(FitImage(source=bg_image_path))

        # 2. Main Layout
        self.root_layout = MDFloatLayout()
        
        # Container for alignment
        self.login_container = MDFloatLayout(
            size_hint=(None, None),
            size=(dp(310), dp(520)), 
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # 3. Duck Character
        duck_img_path = os.path.join(ASSETS_DIR, 'tatalog.png')
        self.duck_image = Image(
            source=duck_img_path,
            size_hint=(None, None),
            size=(dp(120), dp(120)),
            pos_hint={'center_x': 0.5, 'top': 1} 
        )
        
        # 4. Login Card
        self.card = MDCard(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(310), dp(440)), 
            pos_hint={'center_x': 0.5, 'y': 0},
            radius=[dp(20)],
            padding=dp(25),
            spacing=dp(15),
            md_bg_color=COLOR_CARD_BG,
            elevation=0 
        )
        
        # Username Field
        self.user_field = MDTextField(
            mode="round",
            fill_color_normal=[1, 1, 1, 1],
            fill_color_focus=[1, 1, 1, 1],
            icon_left="account",
            font_name='chinese_font',
            font_name_hint_text='chinese_font',
            size_hint_x=1,
        )
        self.user_field.line_color_normal = [0, 0, 0, 0]
        self.user_field.line_color_focus = [0, 0, 0, 0]
        self.user_field.bind(text=self.on_field_text)

        # Password Field
        self.pass_field = MDTextField(
            mode="round",
            password=True,
            fill_color_normal=[1, 1, 1, 1],
            fill_color_focus=[1, 1, 1, 1],
            icon_left="lock",
            font_name='chinese_font',
            font_name_hint_text='chinese_font',
            size_hint_x=1,
        )
        self.pass_field.line_color_normal = [0, 0, 0, 0]
        self.pass_field.line_color_focus = [0, 0, 0, 0]
        self.pass_field.bind(text=self.on_field_text)

        # Remember Me
        self.remember_layout = MDBoxLayout(
            orientation='horizontal',
            adaptive_height=True,
            spacing=dp(5),
            padding=[dp(0), dp(5), dp(0), dp(5)]
        )
        
        self.remember_check = MDCheckbox(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_y': .5}
        )
        
        self.remember_label = MDLabel(
            text="Remember me",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_DARK_GREY,
            pos_hint={'center_y': .5},
            font_name='chinese_font',
            font_style="Caption"
        )
        
        self.remember_layout.add_widget(self.remember_check)
        self.remember_layout.add_widget(self.remember_label)
        
        # Login Button Container (to ensure width)
        self.btn_container = MDBoxLayout(size_hint_y=None, height=dp(50))
        self.login_btn = MDFillRoundFlatButton(
            text="Log In",
            size_hint=(1, 1),
            on_release=self.do_login,
            font_name='chinese_font',
            md_bg_color=COLOR_LOGIN_BTN,
            text_color=COLOR_LOGIN_BTN_TEXT,
            font_size="18sp"
        )
        self.btn_container.add_widget(self.login_btn)
        
        # Bottom Links (Sign Up centered)
        self.links_layout = MDBoxLayout(
            orientation='horizontal',
            adaptive_height=True,
            pos_hint={'center_x': 0.5}
        )
        
        self.register_link = MDTextButton(
            text="Sign Up",
            theme_text_color="Custom",
            text_color=COLOR_TEXT_DARK_GREY,
            on_release=self.do_register,
            font_name='chinese_font',
            font_size="15sp",
            pos_hint={'center_x': 0.5}
        )
        
        # Spacer to center the link
        self.links_layout.add_widget(MDLabel(size_hint_x=0.5))
        self.links_layout.add_widget(self.register_link)
        self.links_layout.add_widget(MDLabel(size_hint_x=0.5))

        # Assemble Card
        # self.card.add_widget(MDLabel(size_hint_y=None, height=dp(25))) 
        self.card.add_widget(self.user_field)
        self.card.add_widget(self.pass_field)
        self.card.add_widget(self.remember_layout)
        self.card.add_widget(MDLabel(size_hint_y=None, height=dp(15))) 
        self.card.add_widget(self.btn_container)
        self.card.add_widget(MDLabel(size_hint_y=None, height=dp(25))) 
        self.card.add_widget(self.links_layout)
        
        self.login_container.add_widget(self.card)
        self.login_container.add_widget(self.duck_image) 
        
        self.root_layout.add_widget(self.login_container) 
        
        self.add_widget(self.root_layout)
        self.dialog = None

    def on_field_text(self, instance, value):
        # Force clear hint text if text is present to prevent overlap
        if value:
            if not hasattr(instance, '_current_hint'):
                instance._current_hint = instance.hint_text
            instance.hint_text = ""
        else:
            # Restore hint text if field becomes empty
            if hasattr(instance, '_current_hint'):
                instance.hint_text = instance._current_hint

    def update_theme_colors(self):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        self.md_bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM

    def on_enter(self):
        self.update_theme_colors()
        self.update_ui_text()
        
        def set_saved_creds(dt):
            saved_user = database.get_local_setting("remember_user")
            saved_pass = database.get_local_setting("remember_pass")
            
            if saved_user and saved_pass:
                # Set text carefully to trigger on_field_text
                self.user_field.text = saved_user
                self.pass_field.text = saved_pass
                self.remember_check.active = True
                
        # Small delay to ensure widgets are ready
        Clock.schedule_once(set_saved_creds, 0.2)

    def update_ui_text(self):
        app = MDApp.get_running_app()
        if not hasattr(app, "current_lang"): return
        d = LANG_DICT[app.current_lang]
        
        # Save hints for the manual management
        self.user_field._current_hint = d.get("username", "Username")
        self.pass_field._current_hint = d.get("password", "Password")
        
        # Only update hint_text if field is empty
        if not self.user_field.text:
            self.user_field.hint_text = self.user_field._current_hint
        else:
            self.user_field.hint_text = ""

        if not self.pass_field.text:
            self.pass_field.hint_text = self.pass_field._current_hint
        else:
            self.pass_field.hint_text = ""

        self.login_btn.text = d.get("login", "Log In")
        self.register_link.text = d.get("register", "Sign Up")
        self.remember_label.text = d.get("remember_me", "Remember me")
        
        # Enforce fonts
        self.user_field.font_name = 'chinese_font'
        self.pass_field.font_name = 'chinese_font'
        self.login_btn.font_name = 'chinese_font'
        self.register_link.font_name = 'chinese_font'
        self.remember_label.font_name = 'chinese_font'

    def do_login(self, *args):
        user = self.user_field.text.strip()
        pwd = self.pass_field.text.strip()
        
        if not user or not pwd:
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            self.show_error(d["login_error_empty"])
            return
            
        success = database.login(user, pwd)
        if success:
            if self.remember_check.active:
                database.save_local_setting("remember_user", user)
                database.save_local_setting("remember_pass", pwd)
            else:
                database.save_local_setting("remember_user", "")
                database.save_local_setting("remember_pass", "")
            
            self.go_to_main()
        else:
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            self.show_error(d["login_error_failed"])

    def do_register(self, *args):
        user = self.user_field.text.strip()
        pwd = self.pass_field.text.strip()
        
        if not user or not pwd:
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            self.show_error(d["login_error_empty"])
            return
            
        success = database.register(user, pwd)
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        if success:
            self.show_success(d["register_success"], next_action=self.go_to_main)
        else:
            self.show_error(d["register_failed"])

    def go_to_main(self, *args):
        app = MDApp.get_running_app()
        app.update_all_colors() 
        app.refresh_ui_text() 
        
        from kivymd.uix.transition import MDFadeSlideTransition
        app.screen_manager.transition = MDFadeSlideTransition(duration=0.5)
        app.screen_manager.current = "main"

    def show_error(self, text):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.dialog = MDDialog(
            title=d["error_title"],
            text=text,
            buttons=[MDFlatButton(text=d["ok"], on_release=lambda x: self.dialog.dismiss(), font_name='chinese_font')]
        )
        self.dialog.open()

    def show_success(self, text, next_action=None):
        def on_close(x):
            self.dialog.dismiss()
            if next_action:
                next_action()
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.dialog = MDDialog(
            title=d["success_title"],
            text=text,
            buttons=[MDFlatButton(text=d["ok"], on_release=on_close, font_name='chinese_font')]
        )
        self.dialog.open()
