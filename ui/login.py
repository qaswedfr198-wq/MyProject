from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp
import database
from ui.localization import LANG_DICT

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
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang] if hasattr(app, "current_lang") else {}
        
        # Title
        self.title_label = MDLabel(
            text="Welcome", # Default, updated later
            halign="center",
            font_style="H4",
            size_hint_y=None, 
            height=dp(50)
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
        
        # Buttons
        self.login_btn = MDFillRoundFlatButton(
            text="Login",
            size_hint_x=1,
            on_release=self.do_login
        )
        
        self.register_btn = MDFlatButton(
            text="Register New Account",
            size_hint_x=1,
            on_release=self.do_register
        )
        
        self.guest_btn = MDFlatButton(
            text="Continue as Guest (Offline)",
            size_hint_x=1,
            theme_text_color="Hint",
            on_release=self.do_guest
        )
        
        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.user_field)
        self.layout.add_widget(self.pass_field)
        self.layout.add_widget(self.login_btn)
        self.layout.add_widget(self.register_btn)
        self.layout.add_widget(self.guest_btn)
        
        self.add_widget(self.layout)
        self.dialog = None

    def on_enter(self):
        self.update_ui_text()

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

    def do_login(self, *args):
        user = self.user_field.text.strip()
        pwd = self.pass_field.text.strip()
        
        if not user or not pwd:
            self.show_error("Please enter username and password")
            return
            
        success = database.login(user, pwd)
        if success:
            self.go_to_main()
        else:
            self.show_error("Login failed. Check credentials.")

    def do_register(self, *args):
        user = self.user_field.text.strip()
        pwd = self.pass_field.text.strip()
        
        if not user or not pwd:
            self.show_error("Please enter username and password")
            return
            
        success = database.register(user, pwd)
        if success:
            self.show_success("Account created! Logging in...", next_action=self.go_to_main)
        else:
            self.show_error("Registration failed. Username may be taken.")

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
        self.dialog = MDDialog(
            title="Error",
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

    def show_success(self, text, next_action=None):
        def on_close(x):
            self.dialog.dismiss()
            if next_action:
                next_action()
                
        self.dialog = MDDialog(
            title="Success",
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=on_close)]
        )
        self.dialog.open()
