from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from ui.localization import LANG_DICT

class FamilyCard(MDCard):
    def __init__(self, member_data, delete_callback=None, edit_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.delete_callback = delete_callback
        self.edit_callback = edit_callback
        
        # Data unpacking: id, name, age, gender, allergens, genetic, height, weight
        self.member_id = member_data[0]
        self.name = member_data[1]
        self.age = member_data[2]
        self.gender = member_data[3]
        self.allergens = member_data[4]
        self.genetic = member_data[5]
        self.height_val = member_data[6] or 0
        self.weight_val = member_data[7] or 0
        
        # Calculate BMI
        bmi_text = "--"
        if self.height_val > 0 and self.weight_val > 0:
            h_m = self.height_val / 100
            bmi = self.weight_val / (h_m * h_m)
            bmi_text = f"{bmi:.1f}"

        self.size_hint_y = None
        self.height = dp(100)
        self.radius = [12]
        self.padding = [dp(12), dp(8)]
        self.spacing = dp(2)
        self.elevation = 0 
        self.orientation = "vertical"
        self.ripple_behavior = True
        
        # Dynamic theme colors with 80% Opacity (0.8 alpha)
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        d = LANG_DICT[app.current_lang]
        
        self.md_bg_color = [0.15, 0.15, 0.15, 0.8] if is_dark else [1, 1, 1, 0.8]
        self.line_color = [1, 1, 1, 0.1] if is_dark else [0, 0, 0, 0.1]
        self.line_width = 1
        
        text_color = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        secondary_text = [0.8, 0.8, 0.8, 1] if is_dark else [0.5, 0.5, 0.5, 1]
        
        # Condensed Stat Helper
        def create_mini_stat(label, value):
            box = MDBoxLayout(orientation='horizontal', spacing=dp(4), adaptive_width=True)
            box.add_widget(MDLabel(
                text=label + ":", 
                font_style="Caption", 
                theme_text_color="Custom",
                text_color=secondary_text,
                adaptive_width=True
            ))
            box.add_widget(MDLabel(
                text=str(value), 
                font_style="Caption", 
                bold=True, 
                theme_text_color="Custom",
                text_color=text_color,
                adaptive_width=True
            ))
            return box

        # --- ROW 1: Header (Name, Gender, Edit, Delete) ---
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(5))
        
        icon_name = "gender-male" if str(self.gender).lower().startswith("m") or self.gender == "Male" else "gender-female"
            
        name_lbl = MDLabel(
            text=self.name, 
            font_size="17sp",
            bold=True, 
            theme_text_color="Custom",
            text_color=text_color,
            shorten=True
        )
        
        sex_icon = MDIconButton(
            icon=icon_name, 
            theme_text_color="Custom",
            text_color=secondary_text,
            icon_size="16sp",
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            pos_hint={'center_y': 0.5}
        )
        
        edit_btn = MDIconButton(
            icon="pencil-outline",
            theme_text_color="Custom",
            text_color=secondary_text,
            icon_size="16sp",
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            on_release=lambda x: self.edit_callback(member_data) if self.edit_callback else None,
            pos_hint={'center_y': 0.5}
        )

        delete_btn = MDIconButton(
            icon="delete-outline", 
            theme_text_color="Custom",
            text_color=secondary_text,
            icon_size="16sp",
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            on_release=lambda x: self.delete_callback(self.member_id, self.name) if self.delete_callback else None,
            pos_hint={'center_y': 0.5}
        )
        
        header.add_widget(name_lbl)
        header.add_widget(sex_icon)
        header.add_widget(edit_btn)
        header.add_widget(delete_btn)
        
        # --- ROW 2: Stats Row (Age, H, W, BMI) ---
        row2 = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(20))
        row2.add_widget(create_mini_stat(d["age"], self.age))
        row2.add_widget(create_mini_stat("H", f"{int(self.height_val)}"))
        row2.add_widget(create_mini_stat("W", f"{self.weight_val:.1f}"))
        row2.add_widget(create_mini_stat("BMI", bmi_text))
        
        # --- ROW 3: Care info (Allergens + Genetic) ---
        footer = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(18))
        care_items = []
        if self.allergens: care_items.append(f"{d['allergens'].split()[0]}: {self.allergens}")
        if self.genetic: care_items.append(f"{d['genetic'].split()[0]}: {self.genetic}")
        
        care_text = " | ".join(care_items) if care_items else d.get("none", "No specific care")
            
        care_lbl = MDLabel(
            text=care_text,
            font_size="10sp",
            theme_text_color="Custom",
            text_color=secondary_text,
            shorten=True,
            halign="left"
        )
        footer.add_widget(care_lbl)

        self.add_widget(header)
        self.add_widget(row2)
        self.add_widget(footer)

from kivymd.uix.selectioncontrol import MDCheckbox

class InventoryCard(MDCard):
    def __init__(self, item_data, delete_callback=None, checkbox_callback=None, edit_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.delete_callback = delete_callback
        self.checkbox_callback = checkbox_callback
        self.edit_callback = edit_callback
        self.item_full_data = item_data # Keep reference for edit
        
        # item_id, name, qty, unit, expiry_date, buy_date, area
        self.item_id = item_data[0]
        self.name = item_data[1]
        self.qty = item_data[2]
        self.unit = item_data[3] or "unit" # Handle None
        self.expiry = item_data[4]
        self.buy_date = item_data[5] 
        self.area = item_data[6]

        self.size_hint_y = None
        self.height = dp(80)
        self.radius = [12]
        self.padding = [dp(5), dp(5)] # Reduced padding to accommodate checkbox
        self.spacing = dp(2)
        self.elevation = 0
        self.orientation = "horizontal"
        self.ripple_behavior = True
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        is_dark = app.theme_cls.theme_style == "Dark"
        
        # 80% Opacity (0.8 alpha)
        self.md_bg_color = [0.15, 0.15, 0.15, 0.8] if is_dark else [1, 1, 1, 0.8]
        self.line_color = [1, 1, 1, 0.1] if is_dark else [0, 0, 0, 0.1]
        self.line_width = 1
        
        text_color = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        secondary_text = [0.8, 0.8, 0.8, 1] if is_dark else [0.5, 0.5, 0.5, 1]

        # Left Checkbox
        self.checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={'center_y': 0.5},
            active=False
        )
        self.checkbox.bind(active=self.on_checkbox_active)
        self.add_widget(self.checkbox)

        # Content
        content = MDBoxLayout(orientation='vertical', spacing=dp(2), pos_hint={'center_y': 0.5})
        
        title_box = MDBoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(25))
        title_box.add_widget(MDLabel(
            text=f"{self.name}",
            bold=True,
            font_size="16sp",
            theme_text_color="Custom",
            text_color=text_color,
            font_name='chinese_font'
        ))
        
        # Display Quantity + Unit
        unit_key_map = {
            'g': 'short_unit_g',
            'kg': 'short_unit_kg',
            'ml': 'short_unit_ml',
            'l': 'short_unit_l',
            'unit': 'short_unit_pc'
        }
        # Get localized unit string
        # Default to raw self.unit if not mapped
        u_key = unit_key_map.get(self.unit, '')
        unit_display = d.get(u_key, self.unit) if u_key else self.unit
        
        title_box.add_widget(MDLabel(
            text=f"x{self.qty} {unit_display}",
            font_size="14sp",
            theme_text_color="Custom",
            text_color=secondary_text,
            halign="right"
        ))
        
        sub_box = MDBoxLayout(orientation='horizontal', spacing=dp(10))
        
        app = MDApp.get_running_app()
        # d is already defined
        
        buy_lbl = d.get('short_buy', 'Buy')
        exp_lbl = d.get('short_exp', 'Exp')
        
        # Bubble Helper
        def create_bubble(text, color_bg):
            card = MDCard(
                size_hint=(None, None),
                height=dp(22),
                radius=[6],
                md_bg_color=color_bg,
                padding=[dp(6), dp(2)],
                elevation=0,
                adaptive_width=True,
                pos_hint={'center_y': 0.5}
            )
            card.add_widget(MDLabel(
                text=text,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=text_color,
                adaptive_size=True,
                font_name='chinese_font',
                bold=True,
                valign='middle'
            ))
            return card

        # Bubble Colors
        bubble_bg = [0.25, 0.25, 0.25, 1] if is_dark else [0.9, 0.9, 0.9, 1] # Subtle grey
        
        # Add Bubbles
        if self.buy_date:
            sub_box.add_widget(create_bubble(f"{buy_lbl}: {self.buy_date}", bubble_bg))
            
        sub_box.add_widget(create_bubble(f"{exp_lbl}: {self.expiry}", bubble_bg))
        
        # Area bubble with slightly different color or same
        sub_box.add_widget(create_bubble(self.area, bubble_bg))
        
        content.add_widget(title_box)
        content.add_widget(sub_box)
        self.add_widget(content)

        # Right Actions
        actions = MDBoxLayout(orientation='horizontal', size_hint_x=None, width=dp(80), pos_hint={'center_y': 0.5})
        
        # Edit Button
        actions.add_widget(MDIconButton(
            icon="pencil-outline",
            theme_text_color="Custom",
            text_color=secondary_text,
            pos_hint={'center_y': 0.5},
            on_release=lambda x: self.edit_callback(self.item_full_data) if self.edit_callback else None
        ))

        # Delete Button
        actions.add_widget(MDIconButton(
            icon="delete-outline",
            theme_text_color="Custom",
            text_color=secondary_text,
            pos_hint={'center_y': 0.5},
            on_release=lambda x: self.delete_callback(self.item_id) if self.delete_callback else None
        ))
        
        self.add_widget(actions)

    def on_checkbox_active(self, checkbox, value):
        if self.checkbox_callback:
            self.checkbox_callback(self.item_id, value)
