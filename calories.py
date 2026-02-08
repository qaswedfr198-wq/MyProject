import sqlite3
import random
from datetime import datetime, timedelta
from io import BytesIO

# Kivy Configuration (Must be before other Kivy imports)
from kivy.config import Config
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

# Global Font Registration
for name in [FONT_MAIN, 'Roboto']:
    LabelBase.register(name=name, fn_regular='C:/Windows/Fonts/msjh.ttc', fn_bold='C:/Windows/Fonts/msjhbd.ttc')

# Matplotlib Style
plt.rcParams['font.sans-serif'] = [FONT_MAIN]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['text.color'] = '#5C5C5C'
plt.rcParams['axes.labelcolor'] = '#5C5C5C'
plt.rcParams['xtick.color'] = '#5C5C5C'
plt.rcParams['ytick.color'] = '#5C5C5C'

class DatabaseManager:
    def __init__(self, db_name='calories.db'):
        self.db_name = db_name
        self._create_tables()

    def _execute(self, query, params=(), fetch_one=False, fetch_all=False):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch_one: return cursor.fetchone()
            if fetch_all: return cursor.fetchall()
            return cursor.lastrowid

    def _create_tables(self):
        self._execute('''CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, meal_type TEXT, calories INTEGER, note TEXT)''')
        self._execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')


    def get_api_key(self):
        return None # No longer used

    def add_record(self, meal, cal, note=""):
        today = datetime.now().strftime('%Y-%m-%d')
        self._execute('INSERT INTO records (date, meal_type, calories, note) VALUES (?, ?, ?, ?)', (today, meal, cal, note))

    def delete_record(self, rid):
        self._execute('DELETE FROM records WHERE id = ?', (rid,))

    def get_today_total(self):
        today = datetime.now().strftime('%Y-%m-%d')
        res = self._execute('SELECT SUM(calories) FROM records WHERE date = ?', (today,), fetch_one=True)
        return res[0] if res[0] else 0

    def get_today_records(self):
        today = datetime.now().strftime('%Y-%m-%d')
        # Added date column to selection: id, date, meal_type, calories, note
        return self._execute('SELECT id, date, meal_type, calories, note FROM records WHERE date = ?', (today,), fetch_all=True)

    def get_today_breakdown(self):
        today = datetime.now().strftime('%Y-%m-%d')
        rows = self._execute('SELECT meal_type, SUM(calories) FROM records WHERE date = ? GROUP BY meal_type', (today,), fetch_all=True)
        data = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
        for m, c in rows:
            data[m] if m in data else data.update({'snack': data['snack'] + c})
            if m in data: data[m] = c
        return data

    def get_weekly_data(self):
        data = []
        today = datetime.now()
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            res = self._execute('SELECT SUM(calories) FROM records WHERE date = ?', (date,), fetch_one=True)
            label = ["週一","週二","週三","週四","週五","週六","週日"][datetime.strptime(date, '%Y-%m-%d').weekday()]
            data.append({"label": label, "total": res[0] if res[0] else 0})
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
        fig, ax = plt.subplots(figsize=(5, 2))
        fig.patch.set_alpha(0); ax.patch.set_alpha(0)
        
        labels, values = ['早', '午', '晚', '消夜'], [data['breakfast'], data['lunch'], data['dinner'], data['snack']]
        ax.bar(labels, values, color=['#8FBC8F']*3+['#A3CFA3'], alpha=0.8, width=0.5)
        
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#D3D3D3'); ax.spines['bottom'].set_color('#D3D3D3')
        
        # Increase Axis Label Size
        ax.tick_params(axis='x', labelsize=11) 
        ax.tick_params(axis='y', labelsize=10)

        for i, v in enumerate(values):
            if v > 0: ax.text(i, v+10, str(int(v)), ha='center', va='bottom', fontsize=12, fontweight='bold')
        plt.tight_layout()
        return ChartGenerator._render(fig)

    @staticmethod
    def create_weekly(data):
        fig, ax = plt.subplots(figsize=(5, 2))
        fig.patch.set_alpha(0); ax.patch.set_alpha(0)
        
        labels, values = [d['label'] for d in data], [d['total'] for d in data]
        ax.plot(labels, values, color='#8FBC8F', marker='o', lw=2.5)
        ax.fill_between(labels, values, color='#8FBC8F', alpha=0.3)
        
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False); ax.spines['bottom'].set_color('#D3D3D3')
        ax.yaxis.set_visible(False)
        
        # Increase Axis Label Size
        ax.tick_params(axis='x', labelsize=11)

        for i, v in enumerate(values):
            ax.text(i, v+50, str(v), ha='center', fontsize=12, fontweight='bold')
        plt.tight_layout()
        return ChartGenerator._render(fig)

class MainInterface(MDFloatLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.md_bg_color = COLOR_BG_CREAM
        self._build_ui()
        self.refresh_ui()

    def _build_ui(self):
        app = MDApp.get_running_app()
        d = LANG_DICT.get(app.current_lang, LANG_DICT["zh"])
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title=d.get("calories", "Calories"),
            elevation=0,
            pos_hint={'top': 1},
            left_action_items=[["cog", lambda x: app.open_settings()]],
            right_action_items=[["message-text-outline", lambda x: app.switch_to_chat()]],
            md_bg_color=COLOR_BG_CREAM,
            specific_text_color=COLOR_ACCENT_SAGE
        )
        self.add_widget(self.toolbar)

        self.lbl_cal = MDLabel(text="0", halign="center", pos_hint={'center_x': 0.5, 'center_y': 0.82}, 
                               theme_text_color="Custom", text_color=(0.55, 0.45, 0.35, 1), font_style="H3", bold=True)
        self.add_widget(self.lbl_cal)
        
        self.lbl_today = MDLabel(text="今日熱量 (kcal)", halign="center", pos_hint={'center_x': 0.5, 'center_y': 0.89},
                                theme_text_color="Custom", text_color=(0.5, 0.5, 0.5, 1), font_style="Subtitle2")
        self.add_widget(self.lbl_today)

        # 2. Key Content (Cards) - Increased Height
        box = MDBoxLayout(orientation='vertical', size_hint=(0.9, 0.60), pos_hint={'center_x': 0.5, 'y': 0.14}, spacing=dp(12))
        
        self.img_daily = Image(allow_stretch=True, keep_ratio=True)
        self.card_daily = self._create_card("今日熱量", self.img_daily)
        box.add_widget(self.card_daily)
        
        self.img_weekly = Image(allow_stretch=True, keep_ratio=True)
        self.card_weekly = self._create_card("本週趨勢", self.img_weekly)
        box.add_widget(self.card_weekly)
        
        self.add_widget(box)

        # 3. FABs (Add & History)
        # History/Delete - Bottom Left
        self.add_widget(MDFloatingActionButton(icon="history", pos_hint={'x': 0.1, 'y': 0.03}, elevation=0,
                                               md_bg_color=COLOR_ACCENT_SAGE, icon_color=(1,1,1,1), on_release=self.show_history))

        # Add - Bottom Right
        self.add_widget(MDFloatingActionButton(icon="plus", pos_hint={'right': 0.9, 'y': 0.03}, elevation=0, 
                                               md_bg_color=COLOR_ACCENT_SAGE, icon_color=(1,1,1,1), on_release=self.show_add))

    def update_theme_colors(self, *args):
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == "Dark"
        
        # Background
        bg_color = [0.07, 0.07, 0.07, 1] if is_dark else COLOR_BG_CREAM
        self.md_bg_color = bg_color
        
        # Toolbar
        if hasattr(self, 'toolbar'):
            self.toolbar.md_bg_color = [0.12, 0.12, 0.12, 1] if is_dark else COLOR_BG_CREAM
            self.toolbar.specific_text_color = [1, 1, 1, 1] if is_dark else COLOR_TEXT_DARK_GREY
            
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

    def _create_card(self, title, content_widget):
        card = MDCard(radius=[20], elevation=1, md_bg_color=(1, 1, 1, 1), orientation='vertical', padding=dp(10))
        label = MDLabel(text=title, size_hint_y=None, height=dp(20), font_style="Subtitle2", theme_text_color="Custom", text_color=COLOR_TEXT_DARK_GREY)
        card.add_widget(label)
        card.add_widget(content_widget)
        card.label = label
        return card



    def refresh_ui(self):
        # Localization
        app = MDApp.get_running_app()
        d = LANG_DICT[app.current_lang] if hasattr(app, "current_lang") else LANG_DICT["zh"]
        
        self.lbl_today.text = d.get("cal_today", "今日熱量 (kcal)")
        
        total = self.db.get_today_total()
        self.lbl_cal.text = str(total)

        self.img_daily.texture = ChartGenerator.create_daily(self.db.get_today_breakdown())
        self.img_weekly.texture = ChartGenerator.create_weekly(self.db.get_weekly_data())
        
        # Update Cards
        if hasattr(self, 'card_daily'): self.card_daily.label.text = d.get("cal_today", "今日熱量")
        if hasattr(self, 'card_weekly'): self.card_weekly.label.text = d.get("cal_weekly", "本週趨勢")
        if hasattr(self, 'toolbar'): self.toolbar.title = d.get("calories", "Calories")

    # Dialogs
    def show_add(self, _):
        app = MDApp.get_running_app()
        lang = app.current_lang if hasattr(app, "current_lang") else "zh"
        d = LANG_DICT.get(lang, LANG_DICT["zh"])
        
        content = AddFoodContent()
        self.dialog = MDDialog(title=d.get("cal_add_title", "熱量計算機"), type="custom", content_cls=content,
                               buttons=[MDFlatButton(text=d.get("cancel", "取消"), on_release=lambda x: self.dialog.dismiss(), theme_text_color="Custom", text_color=COLOR_TEXT_DARK_GREY),
                                        MDRaisedButton(text=d.get("cal_calculate", "AI 計算"), md_bg_color=COLOR_ACCENT_SAGE, on_release=lambda x: self._on_add(content))])
        self.dialog.open()

    def _on_add(self, content):
        food = content.field.text
        if not food: return
        
        cal = self._call_ai(food)
        if cal is None:
            self.dialog.dismiss()
            # Show error snackbar instead of settings
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="無法估算熱量，請稍後再試", font_name=FONT_MAIN).open()
            return

        self.db.add_record(content.meal, cal, f"AI: {food}")
        self.dialog.dismiss()
        self.refresh_ui()

    def _call_ai(self, food):
        return ai_manager.estimate_calories(food)


    def show_history(self, _):
        app = MDApp.get_running_app()
        lang = app.current_lang if hasattr(app, "current_lang") else "zh"
        d = LANG_DICT.get(lang, LANG_DICT["zh"])
        
        # Fetch records (now includes date at index 1: id, date, meal_type, calories, note)
        records = self.db.get_today_records()
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
            item = TwoLineAvatarIconListItem(
                text=f"{meal_name}: {r[3]} kcal",
                secondary_text=f"{r[1]} | {r[4]}",
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
        
        self.dialog = MDDialog(title=d.get("cal_history", "今日紀錄"), type="custom", content_cls=content,
                               buttons=[MDFlatButton(text=d.get("close", "關閉"), on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

    def _del_record(self, rid):
        self.db.delete_record(rid)
        self.dialog.dismiss()
        self.refresh_ui()
        self.show_history(None)

# Simple Content Classes
class AddFoodContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing="12dp", size_hint_y=None, height="180dp", **kwargs)
        self.meal = 'lunch'
        
        app = MDApp.get_running_app()
        lang = app.current_lang if hasattr(app, "current_lang") else "zh"
        d = LANG_DICT.get(lang, LANG_DICT["zh"])
        
        self.field = MDTextField(hint_text=d.get("cal_input_hint", "輸入食物"), font_name=FONT_MAIN)
        self.add_widget(self.field)
        
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
        self.db = DatabaseManager()
        if self.db.get_today_total() == 0: self.db.add_record('breakfast', 400) # dummy
        return MainInterface(self.db)

    def _configure_fonts(self):
        for style in ["H1", "H2", "H3", "H4", "H5", "H6", "Subtitle1", "Subtitle2", "Body1", "Body2", "Button", "Caption", "Overline"]:
            self.theme_cls.font_styles[style][0] = FONT_MAIN

if __name__ == '__main__':
    CalorieApp().run()
