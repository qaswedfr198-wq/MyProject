from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from ui.localization import LANG_DICT

class FamilyCard(MDCard):
    def __init__(self, member_data, delete_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.delete_callback = delete_callback
        
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
        self.height = dp(230)
        self.radius = [8]
        self.padding = [dp(25), dp(15)]
        self.spacing = dp(12)
        self.elevation = 1
        self.orientation = "vertical"
        self.ripple_behavior = True
        
        # Dynamic theme colors
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        d = LANG_DICT[app.current_lang]
        
        self.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else [1, 1, 1, 1]
        self.line_color = [0.2, 0.2, 0.2, 1] if is_dark else [0.93, 0.93, 0.93, 1]
        text_color = [1, 1, 1, 1] if is_dark else [0.15, 0.15, 0.15, 1]
        secondary_text = [0.9, 0.9, 0.9, 1] if is_dark else [0.6, 0.6, 0.6, 1]
        icon_color = [1, 1, 1, 1] if is_dark else [0.4, 0.4, 0.4, 1]
        
        # Helper to create stat item (Condensed version for Row 2/3)
        def create_stat(label, value):
            box = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(45))
            val_lbl = MDLabel(
                text=str(value), 
                font_style="Subtitle2", 
                bold=True, 
                halign="center",
                theme_text_color="Custom",
                text_color=text_color
            )
            desc_lbl = MDLabel(
                text=label, 
                font_style="Caption", 
                theme_text_color="Custom",
                text_color=secondary_text,
                halign="center"
            )
            box.add_widget(val_lbl)
            box.add_widget(desc_lbl)
            return box

        # --- ROW 1: Header (Name, Gender, Delete) ---
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35))
        
        icon_name = "account"
        if str(self.gender).lower().startswith("m") or self.gender == "Male":
            icon_name = "gender-male"
        elif str(self.gender).lower().startswith("f") or self.gender == "Female":
            icon_name = "gender-female"
            
        name_lbl = MDLabel(
            text=self.name, 
            font_size="18sp",
            bold=True, 
            theme_text_color="Custom",
            text_color=text_color
        )
        
        sex_icon = MDIconButton(
            icon=icon_name, 
            theme_text_color="Custom",
            text_color=secondary_text,
            pos_hint={'center_y': 0.5},
            icon_size="18sp"
        )
        
        delete_btn = MDIconButton(
            icon="delete-outline", 
            theme_text_color="Custom",
            text_color=secondary_text,
            pos_hint={'center_y': 0.5},
            icon_size="18sp"
        )
        if self.delete_callback:
            delete_btn.bind(on_release=lambda x: self.delete_callback(self.member_id, self.name))
        delete_btn.text_color = icon_color # Apply icon_color to delete button
        
        header.add_widget(name_lbl)
        header.add_widget(sex_icon)
        header.add_widget(delete_btn) # Keep original add_widget for delete_btn
        
        # --- ROW 2: Body Stats (H/W/BMI) ---
        row2 = MDGridLayout(cols=3, spacing=dp(10), size_hint_y=None, height=dp(45))
        row2.add_widget(create_stat(d["height"], f"{int(self.height_val)} cm"))
        row2.add_widget(create_stat(d["weight"], f"{self.weight_val:.1f} kg"))
        row2.add_widget(create_stat("BMI", bmi_text))
        
        # --- ROW 3: Age & Care (Age, Allergens, Genetic) ---
        row3 = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(45))
        row3.add_widget(create_stat(d["age"], self.age))
        row3.add_widget(create_stat(d["allergens"].split()[0], self.allergens if self.allergens else "None"))
        
        # Footer Bar for Genetic info (if any) - keeping it clean
        footer = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
        if self.genetic:
             dis_lbl = MDLabel(
                 text=f"• {d['genetic'].split()[0]}: {self.genetic}", 
                 font_style="Caption", 
                 theme_text_color="Custom",
                 text_color=secondary_text,
                 halign="left"
             )
             footer.add_widget(dis_lbl)

        self.add_widget(header)
        self.add_widget(row2)
        self.add_widget(row3)
        self.add_widget(footer)
