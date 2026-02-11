import sqlite3
import os
import random
from datetime import datetime, timedelta
from io import BytesIO
from kivymd.uix.pickers import MDDatePicker

# Kivy Configuration (Must be before other Kivy imports)
from kivy.config import Config
from kivy.utils import platform

if platform != 'android':
    Config.set('graphics', 'width', '400')
    Config.set('graphics', 'height', '600')
    Config.set('graphics', 'resizable', '1')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.graphics import Color, Line
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFloatingActionButton, MDIconButton, MDRaisedButton, MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, TwoLineAvatarIconListItem, IconRightWidget
from kivymd.uix.scrollview import MDScrollView

import ai_manager

from ui.localization import LANG_DICT
from ui.theme import COLOR_BG_CREAM, COLOR_ACCENT_SAGE, COLOR_TEXT_DARK_GREY

# Constants
FONT_MAIN = "Microsoft JhengHei"
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'TATA'))

# Global Font Registration
# Global Font Registration
font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'msjh.ttc')
font_path_bold = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'msjhbd.ttc')
if not os.path.exists(font_path_bold):
    font_path_bold = font_path

for name in [FONT_MAIN, 'Roboto']:
    LabelBase.register(name=name, fn_regular=font_path, fn_bold=font_path_bold)

# Matplotlib Style
plt.rcParams['font.sans-serif'] = [FONT_MAIN]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['text.color'] = '#5C5C5C'
plt.rcParams['axes.labelcolor'] = '#5C5C5C'
plt.rcParams['xtick.color'] = '#5C5C5C'
plt.rcParams['ytick.color'] = '#5C5C5C'







import database

def get_day_breakdown_adapter(date_str=None):
    target_date = date_str if date_str else datetime.now().strftime('%Y-%m-%d')
    rows = database.get_daily_calorie_breakdown(target_date)
    # rows is list of (meal_type, calories)
    data = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
    if rows:
        for m, c in rows:
            # Backend stores strictly localized or English keys?
            # Assuming backend uses English keys 'breakfast', etc. based on previous code.
            # If backend has mixed data, we might need normalization.
            if m in data: data[m] = c
            # If m is "早餐" and we need "breakfast", we need a map.
            # But let's assume consistency for now.
    return data

def get_weekly_data_adapter(end_date_str=None):
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        end_date = datetime.now()
        end_date_str = end_date.strftime('%Y-%m-%d')
        
    # Get raw data from DB: list of (date_str, total_calories)
    # Note: date_str from DB might be date object depending on adapter.
    # RemoteDB (psycopg2) returns date objects. LocalDB (sqlite) returns strings.
    # We should normalize in DB layer or here.
    raw_data = database.get_weekly_calorie_summary(end_date_str)
    
    data_map = {}
    if raw_data:
        for row in raw_data:
            d_val = row[0]
            val = row[1]
            d_str = str(d_val) # Handles both date obj and string
            data_map[d_str] = val
    
    data = []
    for i in range(6, -1, -1):
        d_obj = end_date - timedelta(days=i)
        d_str = d_obj.strftime('%Y-%m-%d')
        val = data_map.get(d_str, 0)
        label = ["週一","週二","週三","週四","週五","週六","週日"][d_obj.weekday()]
        data.append({"label": label, "total": val})
    return data

class ChartGenerator:
    @staticmethod
    def _render(fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', transparent=True)
        buf.seek(0)
        plt.close(fig)
        return CoreImage(buf, ext='png').texture

    @staticmethod
    def create_daily(data):
        fig = plt.figure(figsize=(5, 2), facecolor=(0,0,0,0))
        ax = fig.add_subplot(111, facecolor=(0,0,0,0))
        
        # Ensure figure and axis patches are completely hidden
        fig.patch.set_visible(False)
        ax.patch.set_visible(False)
        
        labels, values = ['早', '午', '晚', '消夜'], [data['breakfast'], data['lunch'], data['dinner'], data['snack']]
        ax.bar(labels, values, color=['#8FBC8F']*3+['#A3CFA3'], alpha=0.8, width=0.5)
        
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#D3D3D3'); ax.spines['bottom'].set_color('#D3D3D3')
        
        ax.tick_params(axis='x', labelsize=11, colors='#555555') 
        ax.tick_params(axis='y', labelsize=10, colors='#555555')

        for i, v in enumerate(values):
            if v > 0: ax.text(i, v+10, str(int(v)), ha='center', va='bottom', fontsize=12, fontweight='bold', color='#555555')
        
        plt.tight_layout()
        return ChartGenerator._render(fig)

    @staticmethod
    def create_weekly(data):
        fig = plt.figure(figsize=(5, 2), facecolor=(0,0,0,0))
        ax = fig.add_subplot(111, facecolor=(0,0,0,0))
        
        # Ensure figure and axis patches are completely hidden
        fig.patch.set_visible(False)
        ax.patch.set_visible(False)
        
        labels, values = [d['label'] for d in data], [d['total'] for d in data]
        ax.plot(labels, values, color='#8FBC8F', marker='o', lw=2.5)
        ax.fill_between(labels, values, color='#8FBC8F', alpha=0.3)
        
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False); ax.spines['bottom'].set_color('#D3D3D3')
        ax.yaxis.set_visible(False)
        
        ax.tick_params(axis='x', labelsize=11, colors='#555555')

        for i, v in enumerate(values):
            ax.text(i, v+50, str(v), ha='center', fontsize=12, fontweight='bold', color='#555555')
            
        plt.tight_layout()
        return ChartGenerator._render(fig)

class MainInterface(MDFloatLayout):
    def __init__(self, db=None, **kwargs):
        super().__init__(**kwargs)
        # db parameter is kept for compatibility but ignored
        self.md_bg_color = COLOR_BG_CREAM
        self.selected_date = datetime.now().strftime('%Y-%m-%d') # Default to today
        self._build_ui()
        self.refresh_ui()

    def _build_ui(self):
        app = MDApp.get_running_app()
        d = LANG_DICT.get(app.current_lang, LANG_DICT["zh"])
        
        # Background Image
        self.bg_image = Image(
            source=os.path.join(ASSETS_DIR, "Calories", "Caloriesbackground.png"),
            allow_stretch=True,
            keep_ratio=False,
            opacity=0.4,
            size_hint=(1, 1)
        )
        self.add_widget(self.bg_image)
        # Custom Branded Toolbar (Style matched to Family/Inventory/AI)
        self.toolbar_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(10), 0, dp(10), 0],
            spacing=dp(10),
            pos_hint={'top': 1}
        )
        
        self.left_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "icon8.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=lambda x: self.show_history(x),
            pos_hint={'center_y': 0.5}
        )
        
        # Use MDTextButton for clickable date title
        from kivymd.uix.button import MDTextButton
        self.title_label = MDTextButton(
            text=self.selected_date,
            halign="center",
            font_name='chinese_font',
            font_style="H5",
            pos_hint={'center_y': 0.5},
            on_release=lambda x: self.show_date_picker()
        )
        # Apply custom color manually since MDTextButton doesn't support theme_text_color="Custom" directly in all versions the same way label does, 
        # but we can try setting color in update_theme_colors
        self.title_label.theme_text_color = "Custom"
        
        # Spacer on the right to ensure title centering

        
        self.toolbar_box.add_widget(self.left_btn)
        
        # Spacer
        self.toolbar_box.add_widget(MDBoxLayout())
        
        self.toolbar_box.add_widget(self.title_label)
        
        # Spacer
        self.toolbar_box.add_widget(MDBoxLayout())
        
        # Add new right button
        self.right_btn = MDIconButton(
            icon=os.path.join(ASSETS_DIR, "icon10.png"),
            icon_size=dp(56),
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            on_release=self.show_add,
            pos_hint={'center_y': 0.5}
        )
        self.toolbar_box.add_widget(self.right_btn)
        
        self.add_widget(self.toolbar_box)

        self.lbl_cal = MDLabel(text="0", halign="center", pos_hint={'center_x': 0.5, 'center_y': 0.76}, 
                               theme_text_color="Custom", text_color=(0.55, 0.45, 0.35, 1), font_style="H3", bold=True)
        self.add_widget(self.lbl_cal)
        
        self.lbl_today = MDLabel(text="今日熱量 (kcal)", halign="center", pos_hint={'center_x': 0.5, 'center_y': 0.82},
                                theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1), font_style="Subtitle2")
        self.add_widget(self.lbl_today)

        # 2. Key Content (Cards) - Adjusted position to avoid label overlap
        box = MDBoxLayout(orientation='vertical', size_hint=(0.9, 0.60), pos_hint={'center_x': 0.5, 'y': 0.11}, spacing=dp(12))
        
        self.img_daily = Image(allow_stretch=True, keep_ratio=True)
        self.card_daily = self._create_card("今日熱量", self.img_daily)
        box.add_widget(self.card_daily)
        
        self.img_weekly = Image(allow_stretch=True, keep_ratio=True)
        self.card_weekly = self._create_card("本週趨勢", self.img_weekly)
        box.add_widget(self.card_weekly)
        
        self.add_widget(box)

        # 3. FABs (Add & History)




    def update_theme_colors(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        # Background
        bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        self.md_bg_color = bg_color
        
        # Toolbar
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else COLOR_BG_CREAM
            
        if hasattr(self, 'title_label'):
            self.title_label.theme_text_color = "Custom"
            self.title_label.text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY
            
        # Labels
        if hasattr(self, 'lbl_cal'):
            self.lbl_cal.text_color = [0.9, 0.9, 0.9, 1] if is_dark else (0.55, 0.45, 0.35, 1)
        if hasattr(self, 'lbl_today'):
            self.lbl_today.text_color = [0.7, 0.7, 0.7, 1] if is_dark else (0.5, 0.5, 0.5, 1)
            
        # Cards
        card_bg = [0.15, 0.15, 0.15, 1] if is_dark else [1, 1, 1, 1]
        text_color = [0.9, 0.9, 0.9, 1] if is_dark else COLOR_TEXT_DARK_GREY
        
        if hasattr(self, 'card_daily'):
            self.card_daily.md_bg_color = card_bg
            self.card_daily.label.text_color = text_color
        if hasattr(self, 'card_weekly'):
            self.card_weekly.md_bg_color = card_bg
            self.card_weekly.label.text_color = text_color
            
        # History Button
        if hasattr(self, 'hist_btn'):
            self.hist_btn.text_color = COLOR_ACCENT_SAGE

    def show_date_picker(self):
        try:
            date_obj = datetime.strptime(self.selected_date, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.now()
            
        date_dialog = MDDatePicker(year=date_obj.year, month=date_obj.month, day=date_obj.day)
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        self.selected_date = value.strftime('%Y-%m-%d')
        self.refresh_ui()

    def _create_card(self, title, content_widget):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        # 70% Opacity (0.7 Alpha)
        bg_color = [0.12, 0.12, 0.12, 0.7] if is_dark else [1, 1, 1, 0.7]
        line_color = [1, 1, 1, 0.1] if is_dark else [0, 0, 0, 0.1]
        
        card = MDCard(radius=[15], elevation=0, md_bg_color=bg_color, orientation='vertical', padding=dp(10))
        card.line_color = line_color
        card.line_width = 1
        
        label = MDLabel(
            text=title, 
            size_hint_y=None, 
            height=dp(25), 
            font_style="Subtitle2", 
            theme_text_color="Custom", 
            text_color=[1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY,
            font_name="chinese_font"
        )
        card.add_widget(label)
        card.add_widget(content_widget)
        card.label = label
        return card



    def refresh_ui(self):
        # Localization
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang] if hasattr(app, "current_lang") else LANG_DICT["zh"]
        
        # Simplify title to just date
        if hasattr(self, "title_label"):
            self.title_label.text = self.selected_date
        elif hasattr(self, "toolbar"):
            self.toolbar.title = self.selected_date

        # Simplify label to just "Total (kcal)" or similar
        self.lbl_today.text = "總熱量 (kcal)"
        
        total = database.get_daily_calorie_total(self.selected_date)
        self.lbl_cal.text = str(total)

        self.img_daily.texture = ChartGenerator.create_daily(get_day_breakdown_adapter(self.selected_date))
        self.img_weekly.texture = ChartGenerator.create_weekly(get_weekly_data_adapter(self.selected_date))
        
        # Update Cards - Keep date there for clarity or simplify too? 
        # User said "top text", so maybe cards are fine. But let's simplify daily to just "當日熱量"
        if hasattr(self, 'card_daily'): self.card_daily.label.text = "當日熱量"
        if hasattr(self, 'card_weekly'): self.card_weekly.label.text = d.get("cal_weekly", "本週趨勢")

    # Dialogs
    def show_add(self, _):
        app = MDApp.get_running_app()
        lang = app.current_lang if hasattr(app, "current_lang") else "zh"
        d = LANG_DICT.get(lang, LANG_DICT["zh"])
        
        content = AddFoodContent(camera_callback=self.open_camera)
        self.dialog = MDDialog(title=d.get("cal_add_title", "熱量計算機"), type="custom", content_cls=content,
                               buttons=[MDFlatButton(text=d.get("cancel", "取消"), on_release=lambda x: self.dialog.dismiss(), theme_text_color="Custom", text_color=COLOR_TEXT_DARK_GREY),
                                        MDRaisedButton(text=d.get("cal_calculate", "AI 計算"), md_bg_color=COLOR_ACCENT_SAGE, on_release=lambda x: self._on_add(content))])
        self.dialog.open()

    def open_camera(self, meal_type):
        self.dialog.dismiss()
        self.pending_meal = meal_type
        try:
            from plyer import filechooser
            app = MDApp.get_running_app()
            d = LANG_DICT[app.current_lang]
            filechooser.open_file(
                title=d.get("select_photo", "選擇照片"),
                filters=[("Images", "*.jpg", "*.png", "*.jpeg")],
                on_selection=self.on_camera_selection
            )
        except Exception as e:
            print(f"Camera error: {e}")
            from kivymd.toast import toast
            toast("無法啟動相機")

    def on_camera_selection(self, selection):
        if not selection: return
        image_path = selection[0]
        from kivymd.toast import toast
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        toast(d.get("cal_recognizing", "AI 正在分析食物卡路里..."))
        
        ai_manager.recognize_calories_from_image_async(self.on_camera_result, image_path)

    def on_camera_result(self, result):
        if not result:
            from kivymd.toast import toast
            toast("辨識失敗，請重試")
            return
            
        food_name = result.get("name")
        calories = result.get("calories")
        
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang]
        
        self.confirm_dialog = MDDialog(
            title=d.get("cal_camera", "卡路里照相"),
            text=d.get("confirm_save_cal", "辨識結果: {food}\n預估熱量: {cal} kcal\n是否儲存此次紀錄?").format(food=food_name, cal=calories),
            buttons=[
                MDFlatButton(text=d.get("cancel", "取消"), on_release=lambda x: self.confirm_dialog.dismiss()),
                MDRaisedButton(text=d.get("save", "儲存"), md_bg_color=COLOR_ACCENT_SAGE, 
                               on_release=lambda x: self.save_camera_record(food_name, calories))
            ]
        )
        self.confirm_dialog.open()

    def save_camera_record(self, food, cal):
        self.confirm_dialog.dismiss()
        meal = getattr(self, "pending_meal", "lunch")
        database.add_calorie_record(self.selected_date, meal, f"Camera AI: {food}", cal)
        self.refresh_ui()
        from kivymd.toast import toast
        toast(f"已儲存: {food}")

    def _on_add(self, content):
        food = content.field.text
        if not food: return
        
        meal = content.meal
        
        try:
            self.dialog.dismiss()
            from kivymd.toast import toast
            toast("AI 正在估算熱量...")
            
            # Callback wrapper to include meal and food context
            def callback(cal):
                try:
                    self.on_estimate_complete(cal, meal, food)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    from kivymd.toast import toast
                    toast(f"錯誤: {str(e)}")
                    # Also print to console just in case
                    print(f"[Callback Error] {e}")
                
            ai_manager.estimate_calories_async(callback, food)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_error_dialog(f"系統錯誤: {str(e)}")

    def on_estimate_complete(self, cal, meal, food):
        from kivymd.toast import toast
        if cal is None:
            toast("無法估算熱量，請稍後再試")
            return

        try:
            database.add_calorie_record(self.selected_date, meal, food, cal, f"AI: {food}")
            self.refresh_ui()
            toast(f"已新增: {food} ({cal} kcal)")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_error_dialog(f"新增失敗: {str(e)}")

    def show_error_dialog(self, text):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        self.err_dialog = MDDialog(
            title="錯誤", 
            text=text,
            buttons=[MDFlatButton(text="關閉", on_release=lambda x: self.err_dialog.dismiss())]
        )
        self.err_dialog.open()

    # _call_ai removed as it is no longer used directly


    def show_history(self, _):
        app = MDApp.get_running_app()
        lang = app.current_lang if hasattr(app, "current_lang") else "zh"
        d = LANG_DICT.get(lang, LANG_DICT["zh"])
        
        
        # Fetch records (id, date, meal_type, food_name, calories, note)
        records = database.get_calorie_records(self.selected_date)
        content = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(300))
        scroll = MDScrollView()
        lst = MDList()
        
        if not records: 
            lst.add_widget(OneLineAvatarIconListItem(text=d.get("cal_no_record", "今日尚無紀錄")))
        
        for r in records:
            # Map meal type to localized string
            meal_key = f"cal_{r[2]}"
            meal_name = d.get(meal_key, r[2].upper()) # Fallback to upper case if not found
            
            # Format: 
            # Main: Breakfast: 550
            # Sub: 2026-02-08 | AI: Sandwich
            # records: id, date, meal_type, food_name, calories, note
            item = TwoLineAvatarIconListItem(
                text=f"{meal_name}: {r[4]} kcal",
                secondary_text=f"{r[1]} | {r[3]}",
                theme_text_color="Custom", 
                text_color=COLOR_TEXT_DARK_GREY,
                secondary_theme_text_color="Custom",
                secondary_text_color=(0.6, 0.6, 0.6, 1)
            )
            
            icon = IconRightWidget(icon="trash-can-outline", theme_text_color="Custom", text_color=(1,0.3,0.3,1), 
                                   on_release=lambda x, rid=r[0]: self._del_record(rid))
            item.add_widget(icon)
            lst.add_widget(item)
            
        scroll.add_widget(lst)
        content.add_widget(scroll)
        
        self.dialog = MDDialog(title=f"{self.selected_date} 紀錄", type="custom", content_cls=content,
                               buttons=[MDFlatButton(text=d.get("close", "關閉"), on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def _del_record(self, rid):
        database.delete_calorie_record(rid)
        self.dialog.dismiss()
        self.refresh_ui()
        self.show_history(None)

# Simple Content Classes
class AddFoodContent(MDBoxLayout):
    def __init__(self, camera_callback=None, **kwargs):
        super().__init__(orientation="vertical", spacing="12dp", size_hint_y=None, height="210dp", **kwargs)
        self.meal = 'lunch'
        self.camera_callback = camera_callback
        
        app = MDApp.get_running_app()
        lang = app.current_lang if hasattr(app, "current_lang") else "zh"
        d = LANG_DICT.get(lang, LANG_DICT["zh"])
        
        layout_input = MDBoxLayout(spacing="8dp", size_hint_y=None, height="48dp")
        self.field = MDTextField(hint_text=d.get("cal_input_hint", "輸入食物"), font_name=FONT_MAIN, size_hint_x=0.8)
        self.btn_camera = MDIconButton(icon="camera", pos_hint={'center_y': 0.5}, on_release=lambda x: self.trigger_camera())
        layout_input.add_widget(self.field)
        layout_input.add_widget(self.btn_camera)
        
        self.add_widget(layout_input)
        
        grid = MDBoxLayout(spacing="8dp", size_hint_y=None, height="40dp")
        self.btns = {}
        meals = [('breakfast', d.get('cal_breakfast', '早餐')),
                 ('lunch', d.get('cal_lunch', '午餐')),
                 ('dinner', d.get('cal_dinner', '晚餐')),
                 ('snack', d.get('cal_snack', '消夜'))]
                 
        for k, n in meals:
            b = MDRaisedButton(text=n, size_hint_x=1, elevation=0, theme_text_color="Custom", on_release=lambda x, key=k: self._set_meal(key))
            self.btns[k] = b; grid.add_widget(b)
        self.add_widget(grid); self._update_btns()

    def trigger_camera(self):
        if self.camera_callback:
            self.camera_callback(self.meal)

    def _set_meal(self, k): self.meal = k; self._update_btns()
    def _update_btns(self):
        for k, b in self.btns.items():
            if k == self.meal:
                b.md_bg_color = COLOR_ACCENT_SAGE
                b.text_color = (1, 1, 1, 1)
            else:
                b.md_bg_color = (0.9, 0.9, 0.9, 1)
                b.text_color = COLOR_TEXT_DARK_GREY


class CalorieApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self._configure_fonts()
        # Initialize default dummy data if needed, but handled by DB logic usually
        if database.get_daily_calorie_total(datetime.now().strftime('%Y-%m-%d')) == 0:
             pass # Removed dummy data injection for now to avoid polluting remote DB
        return MainInterface(None)

    def _configure_fonts(self):
        for style in ["H1", "H2", "H3", "H4", "H5", "H6", "Subtitle1", "Subtitle2", "Body1", "Body2", "Button", "Caption", "Overline"]:
            self.theme_cls.font_styles[style][0] = FONT_MAIN

if __name__ == '__main__':
    CalorieApp().run()
