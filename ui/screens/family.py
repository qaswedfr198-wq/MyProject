from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFillRoundFlatButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.clock import Clock
import os
import database
from ui.localization import LANG_DICT
from ui.cards import FamilyCard
from ui.dialogs import AddMemberSheet
from ui.theme import COLOR_BG_CREAM, COLOR_TEXT_DARK_GREY

# Get the base directory for assets relative to this file
# ui/screens/family.py -> ui/screens -> ui -> project_root -> TATA
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'TATA'))

class FamilyScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_theme_colors()
        self.layout = MDBoxLayout(orientation='vertical', spacing=dp(10))
        
        # ScrollView for Family Cards
        self.scroll = MDScrollView()
        self.card_list = MDBoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20), size_hint_y=None)
        self.card_list.bind(minimum_height=self.card_list.setter('height'))
        
        self.scroll.add_widget(self.card_list)
        self.layout.add_widget(self.scroll)
        
        # FAB for Adding Member removed
        
        self.main_float = MDBoxLayout(orientation='vertical')
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Custom Branded Toolbar to allow larger icons
        self.toolbar_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(10), 0, dp(10), 0],
            spacing=dp(10)
        )
        
        self.left_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "member", "icon3.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: MDApp.get_running_app().open_settings(),
            pos_hint={'center_y': 0.5}
        )
        
        self.title_label = MDLabel(
            text=d["family"],
            halign="center",
            font_name='chinese_font',
            font_style="H5",
            pos_hint={'center_y': 0.5}
        )
        
        self.right_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "member", "member.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: self.open_menu(x),
            pos_hint={'center_y': 0.5}
        )
        
        self.toolbar_box.add_widget(self.left_btn)
        self.toolbar_box.add_widget(self.title_label)
        self.toolbar_box.add_widget(self.right_btn)
        
        self.update_theme_colors()
        
        # Background Image
        self.bg_image = Image(
            source=os.path.join(ASSETS_DIR, "member", "memberbackground.png"),
            allow_stretch=True,
            keep_ratio=False,
            opacity=0.4,
            size_hint=(1, 1)
        )
        self.add_widget(self.bg_image)
        
        self.main_float.add_widget(self.toolbar_box)
        self.main_float.add_widget(self.layout)
        
        # Overlay for empty label
        self.overlay = FloatLayout()
        
        self.add_widget(self.main_float)
        self.add_widget(self.overlay)
        self.dialog = None
        self.equipment_dialog = None
        self.menu = None # Initialize menu
        self.load_data()

    def open_menu(self, button):
        if not self.menu:
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            menu_items = [
                {
                    "text": d.get("add_member", "Add Member"),
                    "viewclass": "OneLineListItem",
                    "on_release": lambda: self.menu_callback("add"),
                    "font_name": "chinese_font",
                },
                {
                    "text": d.get("equipment", "Kitchen Equipment"),
                    "viewclass": "OneLineListItem",
                    "on_release": lambda: self.menu_callback("equipment"),
                    "font_name": "chinese_font",
                }
            ]
            self.menu = MDDropdownMenu(
                caller=button,
                items=menu_items,
                width_mult=4,
            )
        self.menu.open()

    def menu_callback(self, action):
        self.menu.dismiss()
        if action == "add":
            self.show_add_dialog()
        elif action == "equipment":
            self.show_equipment_dialog()

    def show_equipment_dialog(self):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # List of supported equipment (Predefined)
        items = ["oven", "microwave", "air_fryer", "pan", "pot", "rice_cooker", "blender"]
        owned = database.get_kitchen_equipment()
        
        # Identify custom items
        custom_items = [item for item in owned if item not in items and item not in [d.get(k, k) for k in items]]
        
        # Root layout for dialog content
        # We use a vertical box: ScrollView (List) + Input Field
        self.eq_root_layout = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(10))
        
        # ScrollView for list
        scroll = MDScrollView(size_hint_y=None, height=dp(300))
        self.eq_list_layout = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(10), padding=dp(10))
        scroll.add_widget(self.eq_list_layout)
        
        self.eq_checks = {} # name -> checkbox
        self.eq_rows = {}   # name -> row widget (for deletion)
        
        # Helper to add a row
        def add_row(key, label_text, is_active=False, is_custom=False):
            row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10))
            check = MDCheckbox(size_hint=(None, None), size=(dp(48), dp(48)), active=is_active)
            row.add_widget(check)
            
            lbl = MDLabel(text=label_text, font_name='chinese_font', halign="left", size_hint_y=None, height=dp(48))
            row.add_widget(lbl)
            
            if is_custom:
                # Add delete button for custom items
                del_btn = MDIconButton(
                    icon="trash-can", 
                    on_release=lambda x: self.delete_custom_equipment(label_text)
                )
                row.add_widget(del_btn)
                
            self.eq_list_layout.add_widget(row)
            self.eq_checks[label_text] = check
            self.eq_rows[label_text] = row

        # Add predefined items
        for item_key in items:
            label_text = d.get(item_key, item_key)
            is_active = label_text in owned
            add_row(item_key, label_text, is_active, is_custom=False)
            
        # Add existing custom items
        for custom_name in custom_items:
            add_row(custom_name, custom_name, True, is_custom=True)
            
        # Input for new custom item (Fixed at bottom)
        input_row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10), padding=(dp(10), 0))
        self.custom_eq_field = MDTextField(
            hint_text=d.get("add_custom_hint", "Add custom..."),
            font_name='chinese_font',
            size_hint_x=0.7
        )
        add_btn = MDIconButton(
            icon="plus",
            on_release=lambda x: self.add_custom_equipment(self.custom_eq_field.text, add_row)
        )
        input_row.add_widget(self.custom_eq_field)
        input_row.add_widget(add_btn)
        
        self.eq_root_layout.add_widget(scroll)
        self.eq_root_layout.add_widget(input_row)

        self.equipment_dialog = MDDialog(
            title=d["equipment"],
            type="custom",
            content_cls=self.eq_root_layout,
            buttons=[
                MDFlatButton(text=d["cancel"], on_release=lambda x: self.equipment_dialog.dismiss()),
                MDRaisedButton(text=d["save"], on_release=lambda x: self.save_equipment())
            ]
        )
        self.equipment_dialog.open()

    def add_custom_equipment(self, name, add_row_callback):
        name = name.strip()
        if not name: return
        
        if name in self.eq_checks:
            self.eq_checks[name].active = True
        else:
            # callback checks: key, label, is_active, is_custom
            add_row_callback(name, name, True, True)
            
        self.custom_eq_field.text = ""

    def delete_custom_equipment(self, name):
        if name in self.eq_rows:
            self.eq_list_layout.remove_widget(self.eq_rows[name])
            del self.eq_rows[name]
        
        if name in self.eq_checks:
            del self.eq_checks[name]

    def save_equipment(self):
        selected = [name for name, check in self.eq_checks.items() if check.active]
        database.update_kitchen_equipment(selected)
        self.equipment_dialog.dismiss()
        from kivymd.toast import toast
        toast(LANG_DICT[MDApp.get_running_app().current_lang]["save_success"])

    def update_theme_colors(self, *args):
        is_dark = MDApp.get_running_app().theme_cls.theme_style == "Dark"
        # Light Mode: Cream BG, Dark Mode: Dark gray
        self.md_bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else COLOR_BG_CREAM
            
        if hasattr(self, 'title_label'):
            self.title_label.theme_text_color = "Custom"
            self.title_label.text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY

        if hasattr(self, 'empty_label') and self.empty_label:
            text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]
            self.empty_label.theme_text_color = "Custom"
            self.empty_label.text_color = text_color

    def load_data(self):
        self.card_list.clear_widgets()
        members = database.get_family_members()
        
        if not members:
            app = MDApp.get_running_app()
            is_dark = app.theme_cls.theme_style == "Dark"
            d = LANG_DICT[app.current_lang]
            text_color = [1, 1, 1, 1] if is_dark else [0.2, 0.2, 0.2, 1]
            
            if not hasattr(self, 'empty_label') or self.empty_label is None:
                self.empty_label = MDLabel(
                    text=d["no_members"],
                    halign="center",
                    theme_text_color="Custom",
                    text_color=text_color,
                    font_name='chinese_font',
                    pos_hint={'center_x': 0.5, 'center_y': 0.7}
                )
            else:
                self.empty_label.text = d["no_members"] # Update text in case lang changed
                self.empty_label.text_color = text_color
                
            if hasattr(self, 'overlay') and self.empty_label not in self.overlay.children:
                self.overlay.add_widget(self.empty_label)
        else:
            if hasattr(self, 'empty_label') and self.empty_label and hasattr(self, 'overlay') and self.empty_label in self.overlay.children:
                self.overlay.remove_widget(self.empty_label)
        
        for m in members:
            card = FamilyCard(member_data=m, delete_callback=self.confirm_delete_member, edit_callback=self.open_edit_dialog)
            self.card_list.add_widget(card)

    def show_add_dialog(self, instance=None):
        self.dialog = AddMemberSheet(save_callback=self.save_member)
        self.dialog.open()

    def open_edit_dialog(self, member_data):
        self.dialog = AddMemberSheet(save_callback=self.save_member, member_data=member_data)
        self.dialog.open()

    def confirm_delete_member(self, member_id, name):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Use .format() instead of f-string since delete_msg has {name} placeholder
        delete_text = d['delete_msg'].format(name=name)
        
        self.dialog = MDDialog(
            title=d["delete_confirm"],
            text=delete_text,
            buttons=[
                MDFlatButton(text=d["cancel"], on_release=lambda x: self.dialog.dismiss(), theme_text_color="Custom", text_color=COLOR_TEXT_DARK_GREY),
                MDRaisedButton(text=d.get("delete", "刪除"), md_bg_color=[1, 0, 0, 1], on_release=lambda x: self.delete_member(member_id))
            ]
        )
        self.dialog.open()

    def delete_member(self, member_id):
        try:
            database.delete_family_member(member_id)
            if self.dialog:
                self.dialog.dismiss()
            self.load_data()
        except Exception as e:
            print(f"Error deleting family member: {e}")
            import traceback
            traceback.print_exc()
            if self.dialog:
                self.dialog.dismiss()
            from kivymd.toast import toast
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            toast(d.get("error", "刪除失敗，請重試"))

    def save_member(self, member_id, name, age, gender, allergens, genetic, height, weight):
        if member_id:
            # Update existing
            database.update_family_member(member_id, name, age, gender, allergens, genetic, height, weight)
        else:
            # Add new
            database.add_family_member(name, age, gender, allergens, genetic, height, weight)
        
        self.load_data()
        
        from kivymd.toast import toast
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        toast(d.get("save_success", "Success"))

