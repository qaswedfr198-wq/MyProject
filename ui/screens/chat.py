from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDIconButton, MDFillRoundFlatButton, MDFlatButton, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
import os
import json
from datetime import datetime
import database
import ai_manager
from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_ACCENT_SAGE, COLOR_TEXT_DARK_GREY

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'TATA'))

class SuggestionChip(MDFillRoundFlatButton):
    def __init__(self, text, message, is_custom=False, reply_id=None, **kwargs):
        kwargs.setdefault('font_name', 'chinese_font')
        super().__init__(**kwargs)
        self.text = text
        self.message = message
        self.is_custom = is_custom
        self.reply_id = reply_id
        self.md_bg_color = [0.95, 0.95, 0.95, 1]
        self.text_color = [0.4, 0.4, 0.4, 1]
        self.elevation = 0
        self.padding = [dp(10), dp(5)]
        self.size_hint_x = None  # Allow width to be calculated from text
        
        self.long_press_duration = 1.0
        self._long_press_event = None

    def on_touch_down(self, touch):
        if self.is_custom and self.collide_point(*touch.pos):
            self._long_press_event = Clock.schedule_once(
                lambda dt: self.on_long_press(), self.long_press_duration
            )
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._long_press_event:
            Clock.unschedule(self._long_press_event)
            self._long_press_event = None
        return super().on_touch_up(touch)

    def on_long_press(self):
        app = MDApp.get_running_app()
        # Access ai_layout directly from the app instance (set in main.py)
        if hasattr(app, 'ai_layout'):
            app.ai_layout.show_suggestion_mgmt_menu(self)
        else:
            # Fallback traversal
            p = self.parent
            while p and p.__class__.__name__ != 'AIChatScreen':
                p = p.parent
            if p:
                p.show_suggestion_mgmt_menu(self)

class ChatBubble(MDCard):
    def __init__(self, text, sender="You", **kwargs):
        super().__init__(**kwargs)
        self.raw_text = text
        self.recipes_data = []
        
        # Parse ingredients JSON if present
        display_text = text
        if "[INGREDIENTS_JSON]" in text:
            try:
                parts = text.split("[INGREDIENTS_JSON]")
                display_text = parts[0].strip()
                json_str = parts[1].strip()
                self.recipes_data = json.loads(json_str)
            except Exception as e:
                print(f"[ChatBubble] Error parsing ingredients: {e}")
                
        self.radius = [15, 15, 15, 15]
        self.elevation = 0
        self.padding = dp(10)
        self.spacing = dp(5)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(60) # Initial guess
        # Allow width to fill but with margins
        self.size_hint_x = 0.85 
        
        # Determine style based on sender
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        if sender == "You":
            self.md_bg_color = [0.9, 0.9, 0.9, 0.5] if not is_dark else [0.2, 0.2, 0.2, 0.5]
            self.pos_hint = {'right': 0.98}
            align = "right"
            text_color = [0.1, 0.1, 0.1, 1] if not is_dark else [0.9, 0.9, 0.9, 1]
            title_color = COLOR_ACCENT_SAGE
        else:
            self.md_bg_color = [1, 1, 1, 0.5] if not is_dark else [0.15, 0.15, 0.15, 0.5]
            self.pos_hint = {'x': 0.02}
            align = "left"
            text_color = [0.2, 0.2, 0.2, 1] if not is_dark else [0.9, 0.9, 0.9, 1]
            title_color = [0.5, 0.5, 0.5, 1]

        # Title (Sender)
        self.title = MDLabel(
            text=sender, 
            font_style="Caption", 
            theme_text_color="Custom", 
            text_color=title_color,
            size_hint_y=None, 
            height=dp(15),
            halign=align
        )
        self.add_widget(self.title)
        
        # Content
        self.label = MDLabel(
            text=display_text,
            theme_text_color="Custom",
            text_color=text_color,
            size_hint_y=None,
            font_name='chinese_font',
            markup=True
        )
        # 綁定 texture_size 以自動調整高度
        self.label.bind(texture_size=self.update_height)
        self.add_widget(self.label)
        
        # Add Recipe Buttons if data found
        if self.recipes_data:
            btn_box = MDBoxLayout(orientation="vertical", spacing=dp(5), adaptive_height=True, padding=[0, dp(5), 0, 0])
            for recipe in self.recipes_data:
                recipe_name = recipe.get("name", "查看食材")
                btn = MDFillRoundFlatButton(
                    text=f"{recipe_name}",
                    font_name='chinese_font',
                    size_hint_x=1,
                    md_bg_color=COLOR_ACCENT_SAGE,
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x, r=recipe: self.on_recipe_click(r)
                )
                btn_box.add_widget(btn)
            self.add_widget(btn_box)
        
        # Trigger initial height calculation
        Clock.schedule_once(lambda dt: self.update_height(), 0)

    def on_recipe_click(self, recipe_data):
        app = MDApp.get_running_app()
        if hasattr(app, "ai_layout"):
            app.ai_layout.show_chat_recipe_detail(recipe_data)

    def update_height(self, *args):
        self.label.height = self.label.texture_size[1]
        extra_height = dp(25)
        # Account for recipe buttons
        if self.recipes_data:
            extra_height += dp(50) * len(self.recipes_data)
        self.height = self.label.height + self.title.height + extra_height

class AIChatScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._long_press_active_chips = set() # Track chips in long-press state
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Background Image
        bg_image = Image(
            source=os.path.join(ASSETS_DIR, "去背", "10.png"), 
            opacity=0.2,
            size_hint=(0.95, 0.95),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True
        )
        self.add_widget(bg_image)

        # Content Layout (Foreground)
        self.layout = MDBoxLayout(orientation='vertical')
        
        # Chat History
        # Chat History container needs to be a BoxLayout inside ScrollView for variable height items
        self.chat_scroll = MDScrollView()
        self.chat_list = MDBoxLayout(orientation='vertical', size_hint_y=None, padding=dp(10), spacing=dp(10))
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        self.chat_scroll.add_widget(self.chat_list)
        
        # Custom Suggestions Row (Customized Quick Replies)
        self.custom_scroll = MDScrollView(size_hint_y=None, height=dp(48), do_scroll_x=True, do_scroll_y=False)
        self.custom_list = MDBoxLayout(orientation='horizontal', spacing=dp(8), padding=[dp(10), 0, dp(10), 0], size_hint_x=None, adaptive_width=True)
        self.custom_scroll.add_widget(self.custom_list)
        
        # Input Area
        input_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=dp(5), spacing=dp(5))
        
        # Toggle Suggestions Button removed
        
        self.chat_input = MDTextField(hint_text=d["ask_ai"], mode="fill", font_name='chinese_font', font_name_hint_text='chinese_font')
        # Make input field slightly transparent/white to be readable against background
        self.chat_input.md_bg_color = [1, 1, 1, 0.8] 
        
        send_btn = MDIconButton(
            icon="send", 
            on_release=self.send_ai_message,
            theme_text_color="Custom",
            text_color=COLOR_ACCENT_SAGE
        )
        
        input_box.add_widget(self.chat_input)
        input_box.add_widget(send_btn)
        
        # Custom Branded Toolbar (Style matched to Family/Inventory)
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
            text=d["chat"],
            halign="center",
            font_name='chinese_font',
            font_style="H5", # Matched to Inventory screen
            pos_hint={'center_y': 0.5},
            size_hint_x=1,
            shorten=True,
            max_lines=1
        )
        
        self.right_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "Calories", "icon9.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: self.show_date_picker(),
            pos_hint={'center_y': 0.5}
        )

        self.location_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "icon9.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: self.on_location_click(),
            pos_hint={'center_y': 0.5},
            # theme_text_color="Custom",  # Removed as we use image source
            # text_color=[0.8, 0.4, 0.4, 1] 
        )
        
        self.toolbar_box.add_widget(self.right_btn) # History icon now on the left
        
        self.toolbar_box.add_widget(self.title_label)
        
        self.toolbar_box.add_widget(self.location_btn)
        
        # Add widgets to the content layout
        self.layout.add_widget(self.toolbar_box)
        self.layout.add_widget(self.chat_scroll)
        self.layout.add_widget(self.custom_scroll)         # Visible custom suggestions
        self.layout.add_widget(input_box)
        
        # Add content layout to Screen
        self.add_widget(self.layout)
        
        self.update_theme_colors()
        
        # Initial load logic moved to on_enter

    # toggle_suggestions removed

    def on_enter(self, *args):
        # Automatically load today's history upon entering the screen
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        print(f"AIChatScreen: Entering screen, loading history for {self.selected_date}")
        self.load_chat_history(self.selected_date)
        self.load_suggestions()

    def show_date_picker(self):
        # We switch to a MDList-based dialog to avoid MDDatePicker clipping on mobile
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        dates = database.get_chat_dates()
        
        if not dates:
            from kivymd.toast import toast
            toast("尚無聊天紀錄")
            return

        content = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(300))
        scroll = MDScrollView()
        lst = MDList()
        
        for date_str in dates:
            item = OneLineListItem(
                text=date_str,
                on_release=lambda x, ds=date_str: self.on_date_selected_from_list(ds)
            )
            lst.add_widget(item)
            
        scroll.add_widget(lst)
        content.add_widget(scroll)
        
        self.history_dialog = MDDialog(
            title="選擇歷史日期",
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.history_dialog.dismiss())]
        )
        self.history_dialog.open()

    def on_date_selected_from_list(self, date_str):
        self.selected_date = date_str
        if hasattr(self, 'history_dialog'):
            self.history_dialog.dismiss()
        self.load_chat_history(self.selected_date)

    def on_location_click(self):
        # Mock permission check (Always success for now, or use plyer if needed)
        # In a real app: 
        # try:
        #     from plyer import gps
        #     gps.configure(on_location=self.on_gps_location)
        #     gps.start()
        # except: pass
        
        # Ask to link personal data
        self.show_link_data_dialog()

    def show_link_data_dialog(self):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.link_dialog = MDDialog(
            title="餐廳推薦",
            type="custom",
            content_cls=MDBoxLayout(
                MDLabel(
                    text="是否連動個人健康資料(過敏原、慢性病等)以獲得更精準的推薦？\n(若選擇否，將提供一般大眾美食推薦)",
                    theme_text_color="Secondary",
                    font_name="chinese_font"
                ),
                MDBoxLayout(
                    MDFlatButton(text="取消", font_name='chinese_font', theme_text_color="Custom", text_color=[0.5, 0.5, 0.5, 1], on_release=lambda x: self.link_dialog.dismiss()),
                    MDLabel(size_hint_x=1), # Spacer
                    MDFlatButton(text="否", font_name='chinese_font', on_release=lambda x: self.fetch_restaurant_recommendation(use_data=False)),
                    MDRaisedButton(text="是", font_name='chinese_font', on_release=lambda x: self.fetch_restaurant_recommendation(use_data=True)),
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(50),
                    padding=[0, dp(10), 0, 0]
                ),
                orientation="vertical",
                size_hint_y=None,
                height=dp(180),
                padding=[0, dp(10), 0, 0]
            ),
            buttons=[] # No default buttons
        )
        self.link_dialog.open()

    def fetch_restaurant_recommendation(self, use_data):
        self.link_dialog.dismiss()
        
        # Show loading
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.loading_spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(46), dp(46)),
            pos_hint={'center_x': .5, 'center_y': .5},
            active=True
        )
        self.add_widget(self.loading_spinner)
        
        family_data = []
        if use_data:
            family_data = database.get_family_members()
            
        ai_manager.get_restaurant_recommendation_async(self.on_restaurant_result, family_data)

    def on_restaurant_result(self, result):
        if hasattr(self, 'loading_spinner'):
            self.remove_widget(self.loading_spinner)
            
        if not result or not isinstance(result, dict):
            from kivymd.toast import toast
            toast("AI 推薦失敗，請稍後再試")
            return
            
        recommendation = result.get("recommendation", "")
        search_query = result.get("search_query", "附近美食")
        
        self.show_restaurant_overlay(recommendation, search_query)

    def show_restaurant_overlay(self, recommendation, search_query):
        # Persistent Overlay
        self.rest_overlay = FloatLayout()
        
        # Darkened BG
        bg = MDCard(md_bg_color=[0, 0, 0, 0.8], size_hint=(1, 1), radius=[0])
        self.rest_overlay.add_widget(bg)
        
        # Content Card
        card = MDCard(
            orientation="vertical",
            size_hint=(0.9, None),
            height=dp(350),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=dp(20),
            spacing=dp(15),
            radius=[dp(20)]
        )
        
        # Title
        card.add_widget(MDLabel(
            text="為您推薦", 
            font_style="H5", 
            font_name='chinese_font', 
            halign="center", 
            theme_text_color="Primary",
            adaptive_height=True
        ))
        
        # Recommendation Text
        scroll = MDScrollView()
        lbl = MDLabel(
            text=recommendation, 
            font_name='chinese_font', 
            theme_text_color="Secondary",
            adaptive_height=True
        )
        scroll.add_widget(lbl)
        card.add_widget(scroll)
        
        # Google Maps Button
        btn_layout = MDBoxLayout(spacing=dp(10), adaptive_height=True, orientation="vertical")
        
        map_btn = MDRaisedButton(
            text="開啟 Google Maps",
            font_name='chinese_font',
            md_bg_color=[0.2, 0.6, 1, 1],
            size_hint_x=1,
            on_release=lambda x: self.open_google_maps(search_query)
        )
        
        close_btn = MDFlatButton(
            text="關閉",
            font_name='chinese_font',
            size_hint_x=1,
            on_release=lambda x: self.remove_widget(self.rest_overlay)
        )
        
        btn_layout.add_widget(map_btn)
        btn_layout.add_widget(close_btn)
        card.add_widget(btn_layout)
        
        self.rest_overlay.add_widget(card)
        self.add_widget(self.rest_overlay)
        
        # Auto open maps? Or let user click? 
        # Requirement: "Show maps and display nearby food" -> The overlay allows user to see recommendation text AND open maps.
        # Let's auto open map as per likely intent, but keep overlay open.
        self.open_google_maps(search_query)

    def open_google_maps(self, query):
        import webbrowser
        # Use quote to handle spaces/chinese
        from urllib.parse import quote
        url = f"https://www.google.com/maps/search/?api=1&query={quote(query)}"
        webbrowser.open(url)

    def load_chat_history(self, date_str):
        self.chat_list.clear_widgets()
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Update toolbar title to selected date
        if hasattr(self, "title_label"):
            self.title_label.text = f"{d['chat']} ({date_str})"
        elif hasattr(self, "ai_toolbar"):
            self.ai_toolbar.title = f"{d['chat']} ({date_str})"
        
        history = database.get_chat_history(date_str)
        
        if not history:
            # Show "No records" label if needed?
            pass
        
        for sender, message, timestamp in history:
            bubble = ChatBubble(text=message, sender=sender)
            self.chat_list.add_widget(bubble)
            
        # Scroll to bottom after loading
        Clock.schedule_once(lambda dt: self.chat_scroll.scroll_to(self.chat_list.children[0]) if self.chat_list.children else None, 0.2)

    def load_suggestions(self):
        # 1. Preset Suggestions removed
        self.custom_list.clear_widgets()
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
            
        # 2. Custom Suggestions from DB -> Row 2
        import database
        customs = database.get_quick_replies()
        for r_id, content, *rest in customs:
            label = (content[:8] + '..') if len(content) > 8 else content
            btn = SuggestionChip(text=label, message=content, is_custom=True, reply_id=r_id)
            btn.md_bg_color = [0.9, 0.95, 0.9, 1]
            # Bind normal click to send
            btn.bind(on_release=self.on_chip_release)
            self.custom_list.add_widget(btn)
                
        # 3. Add Custom Button -> Row 2
        add_btn = MDIconButton(icon="plus-circle-outline", theme_text_color="Custom", text_color=[0.5, 0.5, 0.5, 1])
        add_btn.bind(on_release=self.show_add_suggestion_dialog)
        self.custom_list.add_widget(add_btn)

    def on_chip_release(self, instance):
        # Prevent sending message if this was a long-press management action
        if instance in self._long_press_active_chips:
            self._long_press_active_chips.remove(instance)
            return
        self.send_suggestion(instance.message)

    def send_suggestion(self, message):
        self.chat_input.text = message
        self.send_ai_message(None)

    def show_suggestion_mgmt_menu(self, chip):
        self._long_press_active_chips.add(chip)
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        # Using a custom layout to avoid internal KivyMD list item padding bugs in MDDialog
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=dp(5))
        edit_btn = MDRaisedButton(
            text="編輯此詞彙", 
            font_name='chinese_font',
            pos_hint={'center_x': 0.5},
            on_release=lambda x: self.open_edit_dialog(chip)
        )
        delete_btn = MDRectangleFlatButton(
            text="刪除此詞彙", 
            font_name='chinese_font',
            text_color=[0.8, 0, 0, 1],
            line_color=[0.8, 0, 0, 1],
            pos_hint={'center_x': 0.5},
            on_release=lambda x: self.confirm_delete_suggestion(chip)
        )
        content.add_widget(edit_btn)
        content.add_widget(delete_btn)

        self.mgmt_dialog = MDDialog(
            title="管理快捷訊息",
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.mgmt_dialog.dismiss())]
        )
        self.mgmt_dialog.open()

    def open_edit_dialog(self, chip):
        self.mgmt_dialog.dismiss()
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.custom_input = MDTextField(text=chip.message, hint_text=d["ask_ai"], mode="fill", font_name='chinese_font')
        
        self.edit_dialog = MDDialog(
            title="編輯快捷訊息",
            type="custom",
            content_cls=MDBoxLayout(self.custom_input, orientation="vertical", size_hint_y=None, height=dp(60)),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.edit_dialog.dismiss()),
                MDFlatButton(text=d["save"], font_name='chinese_font', on_release=lambda x: self.update_custom_suggestion(chip)),
            ],
        )
        self.edit_dialog.open()

    def update_custom_suggestion(self, chip):
        new_content = self.custom_input.text.strip()
        if new_content:
            import database
            database.delete_quick_reply(chip.reply_id)
            database.add_quick_reply(new_content)
            self.load_suggestions()
        self.edit_dialog.dismiss()

    def confirm_delete_suggestion(self, chip):
        self.mgmt_dialog.dismiss()
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.del_confirm = MDDialog(
            title="確認刪除",
            type="custom",
            content_cls=MDLabel(text=f"確定要刪除「{chip.text}」嗎？", font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.del_confirm.dismiss()),
                MDFlatButton(text="刪除", font_name='chinese_font', theme_text_color="Custom", text_color=[0.8, 0, 0, 1], 
                             on_release=lambda x: self.delete_custom_suggestion(chip)),
            ],
        )
        self.del_confirm.open()

    def delete_custom_suggestion(self, chip):
        import database
        database.delete_quick_reply(chip.reply_id)
        self.load_suggestions()
        self.del_confirm.dismiss()

    def show_add_suggestion_dialog(self, *args):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        self.custom_input = MDTextField(hint_text=d["ask_ai"], mode="fill", font_name='chinese_font')
        
        self.add_dialog = MDDialog(
            title="新增快捷訊息",
            type="custom",
            content_cls=MDBoxLayout(self.custom_input, orientation="vertical", size_hint_y=None, height=dp(60)),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.add_dialog.dismiss()),
                MDFlatButton(text=d["save"], font_name='chinese_font', on_release=self.save_custom_suggestion),
            ],
        )
        self.add_dialog.open()

    def save_custom_suggestion(self, *args):
        content = self.custom_input.text.strip()
        if content:
            import database
            database.add_quick_reply(content)
            self.load_suggestions()
        self.add_dialog.dismiss()

    def update_theme_colors(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        self.md_bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else COLOR_BG_CREAM
            
        if hasattr(self, 'title_label'):
            self.title_label.theme_text_color = "Custom"
            self.title_label.text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY

    def show_chat_recipe_detail(self, recipe_data):
        app = MDApp.get_running_app()
        current_lang = app.current_lang
        d = LANG_DICT[current_lang]
        
        from kivy.uix.scrollview import ScrollView
        content_scroll = ScrollView(size_hint_y=None, height=dp(400))
        layout = MDBoxLayout(orientation="vertical", adaptive_height=True, padding=dp(10), spacing=dp(15))
        
        # Calories
        if recipe_data.get("calories"):
            layout.add_widget(MDLabel(text=f"{d['calories_estimate']}: {recipe_data.get('calories', 0)} kcal", bold=True, font_name='chinese_font', adaptive_height=True))
        
        # Get Current Inventory for Comparison
        inventory = database.get_all_inventory()
        
        # Unify ingredients and shopping_list from recipe_data
        raw_ings = recipe_data.get("ingredients", [])
        raw_shop = recipe_data.get("shopping_list", [])
        
        unique_items = {}
        for i in (raw_ings or []) + (raw_shop or []):
            name = i.get("name") if isinstance(i, dict) else str(i)
            if not name: continue
            if name not in unique_items:
                unique_items[name] = i if isinstance(i, dict) else {"name": name, "qty": 1, "unit": "unit"}

        in_stock_items = []
        missing_items = []

        for name, data in unique_items.items():
            item_name = data.get("name")
            item_qty = data.get("qty", 1)
            item_unit = data.get("unit", "unit")
            
            stock_qty = 0
            found_unit = item_unit
            for inv in inventory:
                inv_name = str(inv[1]).strip().lower()
                if item_name.strip().lower() in inv_name or inv_name in item_name.strip().lower():
                    stock_qty += inv[2]
                    found_unit = inv[3] or item_unit
            
            if stock_qty >= (item_qty if isinstance(item_qty, (int, float)) else 1):
                in_stock_items.append({"data": data, "stock": stock_qty, "stock_unit": found_unit})
            else:
                missing_items.append({"data": data, "stock": stock_qty, "stock_unit": found_unit})

        # --- Sections ---
        
        # 1. Missing Items
        header_missing = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10))
        header_missing.add_widget(MDIcon(icon="cart-outline", theme_text_color="Custom", text_color=[0.8, 0, 0, 1], size_hint=(None, None), size=(dp(24), dp(24))))
        header_missing.add_widget(MDLabel(text="待採買食材", font_style="H6", font_name='chinese_font', adaptive_height=True, text_color=[0.8, 0, 0, 1], theme_text_color="Custom"))
        layout.add_widget(header_missing)
        if not missing_items:
            layout.add_widget(MDLabel(text="• 目前無缺少的食材", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True))
        else:
            for item in missing_items:
                data = item["data"]
                row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(5))
                status_icon = MDIcon(icon="alert-circle-outline", theme_text_color="Custom", text_color=[0.8, 0, 0, 1], size_hint=(None, None), size=(dp(24), dp(24)), pos_hint={'center_y': 0.5})
                
                name_lbl = MDLabel(text=f"{data['name']} {data['qty']}{data['unit']}", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True, pos_hint={'center_y': 0.5})
                
                row.add_widget(status_icon)
                row.add_widget(name_lbl)
                layout.add_widget(row)

        # 2. In Stock items
        header_stock = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10), padding=[0, dp(15), 0, 0])
        header_stock.add_widget(MDIcon(icon="check-circle-outline", theme_text_color="Custom", text_color=[0, 0.6, 0, 1], size_hint=(None, None), size=(dp(24), dp(24))))
        header_stock.add_widget(MDLabel(text="已擁有庫存", font_style="H6", font_name='chinese_font', adaptive_height=True, text_color=[0, 0.6, 0, 1], theme_text_color="Custom"))
        layout.add_widget(header_stock)
        if not in_stock_items:
            layout.add_widget(MDLabel(text="• 目前無現成庫存", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True))
        else:
            for item in in_stock_items:
                data = item["data"]
                row = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(5))
                status_icon = MDIcon(icon="check-circle", theme_text_color="Custom", text_color=[0, 0.7, 0, 1], size_hint=(None, None), size=(dp(24), dp(24)), pos_hint={'center_y': 0.5})
                
                stock_text = f" (庫存: {item['stock']}{item['stock_unit']})"
                name_lbl = MDLabel(text=f"{data['name']} {data['qty']}{data['unit']}{stock_text}", font_name='chinese_font', theme_text_color="Secondary", adaptive_height=True, pos_hint={'center_y': 0.5})
                
                row.add_widget(status_icon)
                row.add_widget(name_lbl)
                layout.add_widget(row)

        # 3. Steps (optional in chat)
        if recipe_data.get("steps"):
            header_steps = MDBoxLayout(orientation="horizontal", adaptive_height=True, spacing=dp(10), padding=[0, dp(15), 0, 0])
            header_steps.add_widget(MDIcon(icon="format-list-bulleted", size_hint=(None, None), size=(dp(24), dp(24))))
            header_steps.add_widget(MDLabel(text="烹飪步驟", font_style="H6", font_name='chinese_font', adaptive_height=True))
            layout.add_widget(header_steps)
            steps_text = "\n\n".join([f"{i+1}. {s}" for i, s in enumerate(recipe_data.get("steps", []))])
            layout.add_widget(MDLabel(text=steps_text, font_name='chinese_font', adaptive_height=True))

        
        content_scroll.add_widget(layout)
        
        self.recipe_detail_dialog = MDDialog(
            title="食譜詳情", # Simpler title
            type="custom",
            content_cls=content_scroll,
            buttons=[
                MDFillRoundFlatButton(
                    text="加入採買", 
                    font_name='chinese_font', 
                    md_bg_color=COLOR_ACCENT_SAGE,
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x: self.add_to_shopping_list_chat(recipe_data)
                ),
                MDFillRoundFlatButton(
                    text="我都煮了", 
                    font_name='chinese_font', 
                    md_bg_color=[1, 0.5, 0, 1], # Orange for "Done" actions
                    text_color=[1, 1, 1, 1],
                    on_release=lambda x: self.cooked_recipe_chat(recipe_data)
                ),
                MDFlatButton(
                    text=d["cancel"], 
                    font_name='chinese_font', 
                    on_release=lambda x: self.recipe_detail_dialog.dismiss()
                )
            ]
        )
        self.recipe_detail_dialog.open()

    def add_single_item_to_shopping_list_chat(self, name, qty, unit):
        try:
            database.add_shopping_item(name, str(qty), unit)
            from kivymd.toast import toast
            toast(f"已加入: {name}")
        except Exception as e:
            print(f"DB Error: {e}")
            from kivymd.toast import toast
            toast(f"加入失敗: {str(e)[:20]}...")

    def add_to_shopping_list_chat(self, recipe_data):
        # 1. Get Unified Items from recipe (same logic as display)
        raw_ings = recipe_data.get("ingredients", [])
        raw_shop = recipe_data.get("shopping_list", [])
        
        unique_items = {}
        for i in (raw_ings or []) + (raw_shop or []):
            name = i.get("name") if isinstance(i, dict) else str(i)
            if not name: continue
            if name not in unique_items:
                unique_items[name] = i if isinstance(i, dict) else {"name": name, "qty": 1, "unit": "unit"}

        # 2. Get Inventory and compare
        inventory = database.get_all_inventory()
        added_count = 0
        
        try:
            for name, data in unique_items.items():
                item_name = data.get("name")
                item_qty = data.get("qty", 1)
                item_unit = data.get("unit", "unit")
                
                # Check stock (similar logic as show_chat_recipe_detail)
                stock_qty = 0
                for inv in inventory:
                    inv_name = str(inv[1]).strip().lower()
                    if item_name.strip().lower() in inv_name or inv_name in item_name.strip().lower():
                        stock_qty += inv[2]
                
                # If stock is insufficient, add to shopping list
                if stock_qty < (item_qty if isinstance(item_qty, (int, float)) else 1):
                    database.add_shopping_item(item_name, str(item_qty), item_unit)
                    added_count += 1
            
            from kivymd.toast import toast
            if added_count > 0:
                toast(f"成功將 {added_count} 項缺漏食材加入清單")
            else:
                toast("庫存充足，無需加入採買清單")
        except Exception as e:
            print(f"DB Error: {e}")
            from kivymd.toast import toast
            toast(f"加入失敗: {str(e)[:20]}...")
        
        self.recipe_detail_dialog.dismiss()

    def cooked_recipe_chat(self, recipe_data):
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        text = f"這將會自動從您的庫存中扣除「{recipe_data.get('name')}」所需的食材份量。確認要繼續嗎？"
        
        self.cook_confirm_dialog = MDDialog(
            title="烹飪確認",
            type="custom",
            content_cls=MDLabel(text=text, font_name='chinese_font', adaptive_height=True),
            buttons=[
                MDFlatButton(text=d["cancel"], font_name='chinese_font', on_release=lambda x: self.cook_confirm_dialog.dismiss()),
                MDRaisedButton(
                    text="確認扣除", 
                    font_name='chinese_font', 
                    md_bg_color=[1, 0.5, 0, 1],
                    on_release=lambda x: self.execute_cook_chat(recipe_data)
                )
            ]
        )
        self.cook_confirm_dialog.open()

    def execute_cook_chat(self, recipe_data):
        from kivymd.toast import toast
        
        ingredients = recipe_data.get("ingredients", [])
        inventory = database.get_all_inventory()
        
        deducted_count = 0
        missing_items = []
        
        for ing in ingredients:
            if not isinstance(ing, dict): continue
            ing_name = str(ing.get("name", "")).strip().lower()
            ing_qty = ing.get("qty", 0)
            ing_unit = str(ing.get("unit", "unit")).strip().lower()
            
            found = False
            for inv_item in inventory:
                inv_name = str(inv_item[1]).strip().lower()
                inv_unit = str(inv_item[3]).strip().lower() if inv_item[3] else "unit"
                
                if ing_name == inv_name or ing_name in inv_name or inv_name in ing_name:
                    if inv_unit == ing_unit:
                        database.update_item_quantity(inv_item[0], -ing_qty)
                        found = True
                        deducted_count += 1
                        break
            if not found:
                missing_items.append(ing.get("name"))
        
        msg = f"已從庫存扣除 {deducted_count} 項食材。"
        if missing_items:
            msg += f"\n未找到: {', '.join(missing_items[:3])}..."
            
        toast(msg)
        self.cook_confirm_dialog.dismiss()
        self.recipe_detail_dialog.dismiss()

    def send_ai_message(self, instance):
        msg = self.chat_input.text
        if not msg: return
        
        # Create User Bubble
        user_bubble = ChatBubble(text=msg, sender="You")
        self.chat_list.add_widget(user_bubble)
        
        # Save to DB
        database.add_chat_message("You", msg)
        
        self.chat_input.text = ""
        self.chat_scroll.scroll_to(user_bubble)
        
        d = LANG_DICT[MDApp.get_running_app().current_lang]
        
        # Show thinking bubble temporarily? Or just a label?
        # A lightweight loading label at bottom
        self.loading_lbl = MDLabel(
            text=d["ai_thinking"], 
            theme_text_color="Secondary", 
            size_hint_y=None, 
            height=dp(30), 
            font_name='chinese_font',
            halign="center"
        )
        self.chat_list.add_widget(self.loading_lbl)
        
        Clock.schedule_once(lambda dt: self.get_ai_response(msg), 0.1)

    def get_ai_response(self, msg):
        try:
            family_data = database.get_family_members()
            inventory_data = database.get_all_inventory()
            equipment_data = database.get_kitchen_equipment()
            
            # Use async method
            ai_manager.get_ai_chat_response_async(self.on_ai_response, msg, family_data, inventory_data, equipment_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.on_ai_response(f"System Error: {str(e)}")

    def on_ai_response(self, response):
        # Remove loading label
        if hasattr(self, 'loading_lbl') and self.loading_lbl in self.chat_list.children:
             self.chat_list.remove_widget(self.loading_lbl)
        
        # Create AI Bubble
        ai_bubble = ChatBubble(text=response, sender="AI Assistant")
        self.chat_list.add_widget(ai_bubble)
        
        # Save to DB
        database.add_chat_message("AI Assistant", response)
        
        # Scroll to bottom
        Clock.schedule_once(lambda dt: self.chat_scroll.scroll_to(ai_bubble), 0.1)
