from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivymd.app import MDApp

# --- KV Styles ---
Builder.load_string('''
<VerticalScrollPicker>:
    canvas.after:
        # Center Highlight Line
        Color:
            rgba: app.theme_cls.primary_color
            a: 0.5
        Line:
            points: [self.x, self.center_y, self.right, self.center_y]
            width: dp(2)

<VerticalScalePicker>:
    canvas.after:
        # Center Indicator (Horizontal line in middle)
        Color:
            rgba: app.theme_cls.text_color
        Line:
            points: [self.x, self.center_y, self.right, self.center_y]
            width: dp(2)

<HorizontalScalePicker>:
    canvas.after:
        # Center Red Indicator
        Color:
            rgba: app.theme_cls.text_color
        Line:
            points: [self.center_x, self.y, self.center_x, self.top]
            width: dp(2)

<GenderItem>:
    elevation: 0
    radius: [20]
    md_bg_color: 
        ([0.2, 0.2, 0.2, 1] if app.theme_cls.theme_style == "Light" else [1, 1, 1, 1]) \
        if self.selected else \
        (app.theme_cls.bg_normal if app.theme_cls.theme_style == "Light" else [0.12, 0.12, 0.12, 1])
    
    orientation: 'vertical'
    padding: "10dp"
    
    canvas.before:
        Color:
            rgba: 
                [0.8, 0.8, 0.8, 0.5] if not self.selected else [0, 0, 0, 0]
        Line:
            width: dp(1)
            rounded_rectangle: (self.x, self.y, self.width, self.height, 20)

    MDIcon:
        icon: root.icon_name
        halign: "center"
        theme_text_color: "Custom"
        text_color: 
            ([0, 0, 0, 1] if app.theme_cls.theme_style == "Light" else [1, 1, 1, 1]) \
            if root.selected else ([0.4, 0.4, 0.4, 1] if app.theme_cls.theme_style == "Light" else [0.7, 0.7, 0.7, 1])
        font_size: "48sp"
        size_hint_y: None
        height: dp(50)
    
    MDLabel:
        text: root.text
        halign: "center"
        bold: True
        theme_text_color: "Custom"
        text_color: 
            ([0, 0, 0, 1] if app.theme_cls.theme_style == "Light" else [1, 1, 1, 1]) \
            if root.selected else ([0.4, 0.4, 0.4, 1] if app.theme_cls.theme_style == "Light" else [0.7, 0.7, 0.7, 1])
        font_name: 'chinese_font'
        size_hint_y: None
        height: dp(30)
''')

class VerticalScalePicker(Widget):
    """
    Vertical scale picker for Height.
    Custom drawing on canvas.
    """
    min_value = NumericProperty(100)
    max_value = NumericProperty(210)
    current_value = NumericProperty(170)
    
    # Scale drawing config
    pixels_per_unit = NumericProperty(dp(10)) # 1 cm = 10dp gap
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, current_value=self.update_canvas)
        self._touch_start_y = 0
        self._value_at_touch_start = 0

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            app = MDApp.get_running_app()
            Color(*app.theme_cls.text_color)
            
            # Value at horizontal center line is self.current_value
            # Height range to draw
            height_val = self.height / 2 / self.pixels_per_unit
            start_val = int(self.current_value - height_val) - 1
            end_val = int(self.current_value + height_val) + 1
            
            for v in range(start_val, end_val + 1):
                if v < self.min_value or v > self.max_value:
                    continue
                
                # Calculate y pos relative to widget y
                diff = v - self.current_value 
                y_pos = self.center_y + (diff * self.pixels_per_unit)
                
                # Length of tick
                if v % 10 == 0:
                    w = dp(60)
                    width = 2
                elif v % 5 == 0:
                    w = dp(40)
                    width = 1.5
                else:
                    w = dp(20)
                    width = 1
                
                # Draw Centered horizontally
                Line(points=[self.center_x - w/2, y_pos, self.center_x + w/2, y_pos], width=width)
                
                # Draw numbers every 10
                if v % 10 == 0:
                    from kivy.core.text import Label as CoreLabel
                    l = CoreLabel(text=str(v), font_size=int(dp(12)), font_name='chinese_font')
                    l.refresh()
                    tex = l.texture
                    # Draw texture to the right of centered tick
                    Color(*app.theme_cls.text_color)
                    Rectangle(texture=tex, pos=(self.center_x + w/2 + dp(5), y_pos - tex.height/2), size=tex.size)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._touch_start_y = touch.y
            self._value_at_touch_start = self.current_value
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            diff_y = touch.y - self._touch_start_y
            # Convert px to value
            val_change = diff_y / self.pixels_per_unit
            
            # Dragging UP (y increases) should subtract from value to scroll UP
            new_val = self._value_at_touch_start - val_change
            self.current_value = max(self.min_value, min(self.max_value, new_val))
            return True
        return super().on_touch_move(touch)
        
    def on_touch_up(self, touch):
        if touch.grab_current == self:
            touch.ungrab(self)
            # Snap to integer
            self.current_value = round(self.current_value)
            return True
        return super().on_touch_up(touch)


class HorizontalScalePicker(Widget):
    """
    Horizontal scale picker for Weight.
    Custom drawing on canvas.
    """
    min_value = NumericProperty(20)
    max_value = NumericProperty(150)
    current_value = NumericProperty(60)
    
    # Scale drawing config
    pixels_per_unit = NumericProperty(dp(10)) # 1 kg = 10dp gap
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, current_value=self.update_canvas)
        # self.bind(on_touch_down=self.on_touch_down, on_touch_move=self.on_touch_move, on_touch_up=self.on_touch_up)
        self._touch_start_x = 0
        self._value_at_touch_start = 0

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            app = MDApp.get_running_app()
            Color(*app.theme_cls.text_color)
            
            # Start drawing based on current_value
            # current_value is at self.center_x
            
            # Range to draw: visible area
            # Value at left edge = current_value - (width/2 / pixels_per_unit)
            
            width_val = self.width / 2 / self.pixels_per_unit
            start_val = int(self.current_value - width_val) - 1
            end_val = int(self.current_value + width_val) + 1
            
            for v in range(start_val, end_val + 1):
                if v < self.min_value or v > self.max_value:
                    continue
                
                # Calculate x pos relative to widget x
                # diff from center
                diff = v - self.current_value 
                x_pos = self.center_x + (diff * self.pixels_per_unit)
                
                # Height of tick
                if v % 10 == 0:
                    h = self.height * 0.5
                    width = 2
                elif v % 5 == 0:
                    h = self.height * 0.3
                    width = 1.5
                else:
                    h = self.height * 0.15
                    width = 1
                
                Line(points=[x_pos, self.y + self.height/2 - h/2, x_pos, self.y + self.height/2 + h/2], width=width)
                
                # Draw numbers every 10
                if v % 10 == 0:
                    # We can't use Labels easily in canvas loop without creating widgets
                    # For performance, maybe just Text Instructions or simple Labels if not too many
                    # Kivy Core Label
                    from kivy.core.text import Label as CoreLabel
                    l = CoreLabel(text=str(v), font_size=int(dp(12)), font_name='chinese_font')
                    l.refresh()
                    tex = l.texture
                    # Draw texture below tick
                    Color(*app.theme_cls.text_color)
                    Rectangle(texture=tex, pos=(x_pos - tex.width/2, self.y), size=tex.size)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._touch_start_x = touch.x
            self._value_at_touch_start = self.current_value
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            diff_x = touch.x - self._touch_start_x
            # Convert px to value
            val_change = diff_x / self.pixels_per_unit
            
            # Dragging right means viewing lower numbers -> Subtract
            new_val = self._value_at_touch_start - val_change
            self.current_value = max(self.min_value, min(self.max_value, new_val))
            return True
        return super().on_touch_move(touch)
        
    def on_touch_up(self, touch):
        if touch.grab_current == self:
            touch.ungrab(self)
            # Snap to integer
            self.current_value = round(self.current_value)
            return True
        return super().on_touch_up(touch)


class GenderItem(MDCard):
    """
    Remove separate ButtonBehavior inheriting.
    MDCard already supports ripple and on_release if ripple_behavior is True (default for some styles)
    or if we use specific behavior mixins. 
    However, Standard MDCard inherits from RectangularRippleBehavior + FloatLayout.
    If we want click events, we usually ensure ripple_behavior is enabled or bind on_touch_down carefully.
    
    Actually in KivyMD 1.x MDCard:
    class MDCard(RectangularRippleBehavior, CommonElevationBehavior, FloatLayout):
    
    So it HAS ripple behavior. But to get 'on_release', we might need to enable it or check collision.
    Actually MDCard does not emit 'on_release' by default unless it's a clickable card type or we mix in ButtonBehavior.
    BUT, mixing ButtonBehavior + MDCard (which has Ripple) caused the MRO issue.
    
    Solution: Just use MDCard and bind on_release? No, MDCard doesn't have on_release event unless it inherits ButtonBehavior.
    
    Alternative: Subclass ButtonBehavior + FloatLayout instead of MDCard if we just want a box? 
    OR: Rely on MDCard's on_touch_down/up to dispatch a custom event?
    
    Let's try standard ButtonBehavior MIXED improperly caused issues?
    The error was: `Cannot create a consistent method resolution order (MRO) for bases ButtonBehavior, MDCard`.
    
    This is because MDCard likely inherits from something that conflicts with ButtonBehavior's place in MRO relative to other bases.
    
    Let's try using `MDCard` replacing `ButtonBehavior`.
    Actually, `MDCard` has `on_release` if `ripple_behavior=True`? No, it's just visual.
    
    Correct approach in KivyMD for clickable card:
    Use `MDCard` and bind `on_touch_down`. Or use `MDCard` with `focus_behavior=True`?
    
    Let's checking KivyMD docs mentally...
    Usually `class MyCard(MDCard):` works fine for clicks if you just bind `on_turn`.
    
    Wait, `ButtonBehavior` + `BoxLayout` is the standard way to make a layout clickable.
    MDCard is a FloatLayout.
    
    Let's go with `class GenderItem(MDCard):` and add `on_touch_down` logic OR just use `MDCard` and hope `on_release` works (it often does not without ButtonBehavior).
    
    Let's try `from kivymd.uix.behaviors import CommonElevationBehavior` etc? No.
    
    Let's Stick to `MDCard`. I will add a simple `on_touch_down` handler if needed, or stick to `ButtonBehavior` but put it AFTER `MDCard`? 
    `class GenderItem(MDCard, ButtonBehavior):` -> MRO error?
    `class GenderItem(ButtonBehavior, MDCard):` -> MRO error?
    
    Let's try: `class GenderItem(MDCard):` and manually implement `on_touch_down`.
    Actually, let's look at `MDCard` source (mental check).
    It inherits `RectangularRippleBehavior`.
    `RectangularRippleBehavior` inherits `CommonRipple`.
    
    If I want `on_release`, I can use `ButtonBehavior` with `BoxLayout` instead of `MDCard`, and just style it like a card.
    BUT `GenderItem` uses `elevation`.
    
    Let's try `class GenderItem(MDCard):` and add `on_touch_down` to dispatch `on_release`?
    Or simpler: The implementation in `GenderSelector` binds `on_release`.
    
    Let's just use `ButtonBehavior` + `BoxLayout` (or `MDBoxLayout`) and manually add background/elevation if needed?
    Or just `MDCard` and use `on_touch_down`.
    
    Wait, the simplest fix for MRO with MDCard is often:
    `class ClickableCard(MDCard)`
    and inside:
    `def on_touch_down(self, touch): ... if collide ... dispatch('on_release') ...`
    
    Actually, let's look at the failing code again.
    `class GenderItem(ButtonBehavior, MDCard):`
    
    I will change it to `class GenderItem(MDCard):` and add a click handler.
    """
    icon_name = StringProperty("account")
    text = StringProperty("")
    selected = BooleanProperty(False)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
            return True
        return super().on_touch_down(touch)

    def on_release(self):
        pass

    # Register event type if not present?
    # MDCard doesn't have on_release event by default.
    # We must register it.
    
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        super().__init__(**kwargs)

class GenderSelector(BoxLayout):
    gender = StringProperty("M") # M or F
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(20)
        self.padding = dp(20)
        
        app = MDApp.get_running_app()
        from main import LANG_DICT
        d = LANG_DICT[app.current_lang]
        
        # Male
        self.male_card = GenderItem(
            icon_name="gender-male",
            text=d["male"],
            selected=(self.gender == "M")
        )
        self.male_card.bind(on_release=lambda x: self.set_gender("M"))
        
        # Female
        self.female_card = GenderItem(
            icon_name="gender-female",
            text=d["female"],
            selected=(self.gender == "F")
        )
        self.female_card.bind(on_release=lambda x: self.set_gender("F"))
        
        self.add_widget(self.male_card)
        self.add_widget(self.female_card)
        self.bind(gender=self.update_selection)

    def set_gender(self, g):
        self.gender = g

    def update_selection(self, *args):
        self.male_card.selected = (self.gender == "M")
        self.female_card.selected = (self.gender == "F")
