from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFillRoundFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp
from ui.localization import LANG_DICT
import components

class PickerSheet(ModalView):
    def __init__(self, title="", picker_cls=None, initial_value=0, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 0.4)
        self.pos_hint = {'bottom': 1}
        self.background_color = [0, 0, 0, 0.5]
        self.callback = callback
        
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        d = LANG_DICT[app.current_lang]
        
        container_bg = [0.15, 0.15, 0.15, 1] if is_dark else [1, 1, 1, 1]
        text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]
        
        container = MDCard(
            orientation="vertical", 
            radius=[20, 20, 0, 0], 
            padding=dp(20),
            spacing=dp(10),
            md_bg_color=container_bg
        )
        
        # Header
        header = MDBoxLayout(size_hint_y=None, height=dp(40))
        header.add_widget(MDLabel(
            text=title, 
            bold=True, 
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=text_color
        ))
        
        # Picker
        self.picker = picker_cls()
        if hasattr(self.picker, 'current_value'):
            self.picker.current_value = initial_value
            
        # Done Button
        btn = MDFillRoundFlatButton(
            text=d["save"], 
            pos_hint={'center_x': 0.5},
            on_release=self.save_and_close
        )
        
        container.add_widget(header)
        container.add_widget(self.picker)
        container.add_widget(btn)
        
        self.add_widget(container)

    def save_and_close(self, *args):
        if self.callback and hasattr(self.picker, 'current_value'):
            self.callback(self.picker.current_value)
        self.dismiss()

class AddMemberSheet(ModalView):
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1) # Full screen or almost full
        self.background = ""
        self.save_callback = save_callback
        
        # Data
        self.gender = "M"
        self.height_val = 170
        self.weight_val = 60.0
        
        # Initialize UI first, then apply colors
        self.layout = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Header
        self.header = MDBoxLayout(size_hint_y=None, height=dp(50))
        self.close_btn = MDIconButton(icon="close", theme_text_color="Custom", on_release=self.dismiss)
        self.title_lbl = MDLabel(text="", halign="center", bold=True, font_style="H5", theme_text_color="Custom")
        self.save_btn = MDIconButton(icon="check", theme_text_color="Custom", on_release=self.save)
        
        self.header.add_widget(self.close_btn)
        self.header.add_widget(self.title_lbl)
        self.header.add_widget(self.save_btn)
        
        # Use ScrollView for Content
        scroll = MDScrollView()
        self.content_box = MDBoxLayout(orientation='vertical', spacing=dp(15), padding=[dp(20), dp(10), dp(20), dp(20)], size_hint_y=None)
        self.content_box.bind(minimum_height=self.content_box.setter('height'))
        
        # Name
        self.name_field = MDTextField(mode="rectangle", font_name='chinese_font', font_name_hint_text='chinese_font')
        self.content_box.add_widget(self.name_field)
        
        # Age
        self.age_field = MDTextField(mode="rectangle", input_filter="int", font_name='chinese_font', font_name_hint_text='chinese_font')
        self.content_box.add_widget(self.age_field)
        
        # Gender
        self.gender_box = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(140), spacing=dp(10))
        self.gender_label = MDLabel(bold=True, theme_text_color="Custom")
        self.gender_box.add_widget(self.gender_label)
        self.gender_box.add_widget(Widget(size_hint_y=None, height=dp(20)))
        
        self.gender_selector = components.GenderSelector()
        self.gender_selector.bind(gender=self.on_gender_change)
        self.gender_box.add_widget(self.gender_selector)
        self.content_box.add_widget(self.gender_box)
        
        # Height Row
        self.height_item = TwoLineAvatarIconListItem(
            secondary_text=f"{self.height_val} cm",
            theme_text_color="Custom",
            secondary_theme_text_color="Custom",
            on_release=self.open_height_picker
        )
        self.height_icon = IconLeftWidget(icon="ruler", theme_text_color="Custom")
        self.height_item.add_widget(self.height_icon)
        self.content_box.add_widget(self.height_item)
        
        # Weight Row
        self.weight_item = TwoLineAvatarIconListItem(
            secondary_text=f"{self.weight_val} kg",
            theme_text_color="Custom",
            secondary_theme_text_color="Custom",
            on_release=self.open_weight_picker
        )
        self.weight_icon = IconLeftWidget(icon="weight-kilogram", theme_text_color="Custom")
        self.weight_item.add_widget(self.weight_icon)
        self.content_box.add_widget(self.weight_item)
        
        # Allergens
        self.allergens_field = MDTextField(mode="rectangle", font_name='chinese_font', font_name_hint_text='chinese_font')
        self.content_box.add_widget(self.allergens_field)
        
        # Genetic
        self.genetic_field = MDTextField(mode="rectangle", font_name='chinese_font', font_name_hint_text='chinese_font')
        self.content_box.add_widget(self.genetic_field)
        
        self.content_box.add_widget(MDBoxLayout(size_hint_y=None, height=dp(20)))
        
        scroll.add_widget(self.content_box)
        self.layout.add_widget(self.header)
        self.layout.add_widget(scroll)
        self.add_widget(self.layout)
        
        self.update_theme_colors()

    def update_theme_colors(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        d = LANG_DICT[app.current_lang]
        
        self.background_color = [0.12, 0.12, 0.12, 1] if is_dark else [1, 1, 1, 1]
        text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]
        
        # Update Text Content
        self.title_lbl.text = d["new_member"]
        self.name_field.hint_text = d["name"]
        self.age_field.hint_text = d["age"]
        self.gender_label.text = d["gender"]
        self.height_item.text = d["height"]
        self.weight_item.text = d["weight"]
        self.allergens_field.hint_text = d["allergens"]
        self.genetic_field.hint_text = d["genetic"]
        
        # Update Colors
        self.title_lbl.text_color = text_color
        self.close_btn.text_color = text_color
        self.save_btn.text_color = text_color
        self.gender_label.text_color = text_color
        
        self.height_item.text_color = text_color
        self.height_item.secondary_text_color = text_color
        self.height_icon.text_color = text_color
        
        self.weight_item.text_color = text_color
        self.weight_item.secondary_text_color = text_color
        self.weight_icon.text_color = text_color

    def on_gender_change(self, instance, value):
        self.gender = value

    def open_height_picker(self, *args):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        sheet = PickerSheet(
            title=d["select_height"],
            picker_cls=components.VerticalScalePicker,
            initial_value=self.height_val,
            callback=self.set_height
        )
        sheet.open()

    def set_height(self, value):
        self.height_val = int(value)
        self.height_item.secondary_text = f"{self.height_val} cm"

    def open_weight_picker(self, *args):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        sheet = PickerSheet(
            title=d["select_weight"],
            picker_cls=components.HorizontalScalePicker,
            initial_value=self.weight_val,
            callback=self.set_weight
        )
        sheet.open()

    def set_weight(self, value):
        self.weight_val = round(value, 1)
        self.weight_item.secondary_text = f"{self.weight_val:.1f} kg"

    def save(self, *args):
        name = self.name_field.text
        if not name: return
        
        try:
            age = int(self.age_field.text) if self.age_field.text else 0
        except ValueError:
            age = 0
        
        self.save_callback(
            name, 
            age,
            self.gender,
            self.allergens_field.text,
            self.genetic_field.text,
            self.height_val,
            self.weight_val
        )
        self.dismiss()
