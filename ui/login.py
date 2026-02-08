from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.metrics import dp
import database
from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_ACCENT_SAGE, COLOR_TEXT_DARK_GREY

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(
            orientation='vertical', 
            spacing=dp(20), 
            padding=dp(40),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            adaptive_height=True
        )
        self.update_theme_colors()
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang] if hasattr(app, "current_lang") else {}
        
        # Title
        self.title_label = MDLabel(
            text="Welcome", # Default, updated later
            halign="center",
            font_style="H4",
            size_hint_y=None, 
            height=dp(50),
            font_name='chinese_font'
        )
        
        # Username
        self.user_field = MDTextField(
            hint_text="Username",
            mode="rectangle",
            font_name='chinese_font',
            font_name_hint_text='chinese_font'
        )
        
        # Password
        self.pass_field = MDTextField(
            hint_text="Password",
            mode="rectangle",
            password=True,
            font_name='chinese_font',
            font_name_hint_text='chinese_font'
        )
        
        # Remember Me Layout
        self.remember_layout = MDBoxLayout(
            orientation='horizontal',
            adaptive_height=True,
            spacing=dp(10),
            padding=[dp(0), dp(10), dp(0), dp(10)]
        )
        
        self.remember_check = MDCheckbox(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_y': .5}
        )
        
        self.remember_label = MDLabel(
            text="Remember Me",
            theme_text_color="Hint",
            pos_hint={'center_y': .5},
            font_name='chinese_font'
        )
        
        self.remember_layout.add_widget(self.remember_check)
        self.remember_layout.add_widget(self.remember_label)
        
        # Buttons
        self.login_btn = MDFillRoundFlatButton(
            text="Login",
            size_hint_x=1,
            on_release=self.do_login,
            font_name='chinese_font',
            md_bg_color=COLOR_ACCENT_SAGE
        )
        
        self.register_btn = MDFlatButton(
            text="Register New Account",
            size_hint_x=1,
            on_release=self.do_register,
            font_name='chinese_font'
        )
        
        self.guest_btn = MDFlatButton(
            text="Continue as Guest (Offline)",
            size_hint_x=1,
            theme_text_color="Hint",
            on_release=self.do_guest,
            font_name='chinese_font'
        )
        
        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.user_field)
        self.layout.add_widget(self.pass_field)
        self.layout.add_widget(self.remember_layout)
        self.layout.add_widget(self.login_btn)
        self.layout.add_widget(self.register_btn)
        self.layout.add_widget(self.guest_btn)
        
        self.add_widget(self.layout)
        self.dialog = None

    def update_theme_colors(self):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        self.md_bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        
        if hasattr(self, 'login_btn'):
            self.login_btn.md_bg_color = [0.2, 0.2, 0.2, 1] if is_dark else COLOR_ACCENT_SAGE
            
        if hasattr(self, 'register_btn'):
           self.register_btn.text_color = [1, 1, 1, 1] if is_dark else COLOR_ACCENT_SAGE
           self.register_btn.theme_text_color = "Custom"

    def on_enter(self):
        self.update_theme_colors()
        self.update_ui_text()
        
        # Check for saved credentials
        saved_user = database.get_local_setting("remember_user")
        saved_pass = database.get_local_setting("remember_pass")
        
        if saved_user and saved_pass:
            self.user_field.text = saved_user
            self.pass_field.text = saved_pass
            self.remember_check.active = True

    def update_ui_text(self):
        app = MDApp.get_running_app()
        if not hasattr(app, "current_lang"): return
        d = LANG_DICT[app.current_lang]
        
        self.title_label.text = d.get("welcome", "Welcome")
        self.user_field.hint_text = d.get("username", "Username")
        self.pass_field.hint_text = d.get("password", "Password")
        self.login_btn.text = d.get("login", "Login")
        self.register_btn.text = d.get("register", "Register")
        self.guest_btn.text = d.get("guest", "Guest Mode")
        self.remember_label.text = d.get("remember_me", "Remember Me")

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

    def do_guest(self, *args):
        database.logout() # Ensure local mode
        self.go_to_main()

    def go_to_main(self, *args):
        app = MDApp.get_running_app()
        # Ensure UI colors are updated based on potentially new settings or defaults
        app.update_all_colors() 
        app.refresh_ui_text() # Refresh text in case language setting was loaded
        
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
