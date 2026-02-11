from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.spinner import MDSpinner
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp

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
