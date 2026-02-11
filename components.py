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
    icon_name = StringProperty("account")
    text = StringProperty("")
    selected = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elevation = 0
        self.radius = [12]
        self.padding = dp(10)
        self.spacing = dp(5)
        self.orientation = 'vertical'
        self.ripple_behavior = True
        self.bind(selected=self.update_color)
        self.update_color()

    def update_color(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        # Selected: Sage Green / Text White
        # Unselected: Transparent / Text Gray
        if self.selected:
            self.md_bg_color = [0.56, 0.74, 0.56, 1] # Simple Sage Green
            self.line_color = [0, 0, 0, 0]
            text_col = [1, 1, 1, 1]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.line_color = [0.8, 0.8, 0.8, 1] if not is_dark else [0.3, 0.3, 0.3, 1]
            text_col = [0.5, 0.5, 0.5, 1]

        self.ids.icon.text_color = text_col
        self.ids.label.text_color = text_col

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
            return True
        return super().on_touch_down(touch)

    def on_release(self):
        pass
        
Builder.load_string('''
<GenderItem>:
    size_hint_y: None
    height: dp(100)
    line_width: 1.2
    
    MDIcon:
        id: icon
        icon: root.icon_name
        halign: "center"
        pos_hint: {'center_x': 0.5}
        theme_text_color: "Custom"
        font_size: "40sp"
    
    MDLabel:
        id: label
        text: root.text
        halign: "center"
        bold: True
        theme_text_color: "Custom"
        font_name: 'chinese_font'
        font_style: "Caption"
''')

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
