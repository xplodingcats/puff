import os
import sys
import subprocess
import sqlite3 # db management
from datetime import datetime
from threading import Thread
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Line, Ellipse # why do i need to import a dot
import serial.tools.list_ports
import matplotlib.pyplot as plt
from openai import OpenAI # for puff cloud ai man
import pyttsx3 # 19 imports is crazy

# Automatic dependency installation
def install_dependencies():
    required = ['kivy', 'matplotlib', 'pyserial', 'openai', 'pyttsx3']
    for package in required:
        try:
            __import__(package.split('==')[0])
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

# Database setup
DB_NAME = "air_quality.db"

# SDS011 Configuration
BAUD_RATE = 9600
SERIAL_TIMEOUT = 2

# UI Configuration
Builder.load_string('''
#:import Factory kivy.factory.Factory

<MainScreen>:
    name: "main"
    BoxLayout:
        orientation: "vertical"
        AirQualityGauge:
            id: gauge
            size_hint: 1, 0.7
        Label:
            text: "PM2.5: " + root.pm25 + "\\nPM10: " + root.pm10
            font_size: '24sp'
            halign: 'center'
            valign: 'middle'

<HistoryScreen>:
    name: "history"
    ScrollView:
        GridLayout:
            id: history_grid
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            row_default_height: '40dp'

<SettingsScreen>:
    name: "settings"
    BoxLayout:
        orientation: "vertical"
        TextInput:
            id: api_key
            hint_text: "OpenAI API Key"
            multiline: False
        FileChooserIconView:
            id: idle_sprite
            filters: ["*.png"]
        FileChooserIconView:
            id: talking_sprite
            filters: ["*.png"]
        ToggleButton:
            text: "Dark Mode"
            on_press: app.toggle_theme()

<OnboardingPopup>:
    title: "Welcome!"
    auto_dismiss: False
    BoxLayout:
        orientation: "vertical"
        Label:
            text: "1. Connect SDS011 sensor\\n2. Enter API key in Settings\\n3. Touch gauge for voice report"
        Button:
            text: "Got it!"
            on_press: root.dismiss()

<GaugePopup>:
    title: "Air Quality Report"
    BoxLayout:
        orientation: "vertical"
        Image:
            id: ai_sprite
            source: "puff_idle.png"
        Label:
            id: report_text
            text: ""
        Button:
            text: "Close"
            on_press: root.dismiss()
''')

class AirQualityGauge(Label):
    value = NumericProperty(0)
    max_value = 300

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(value=self.redraw)
        Clock.schedule_interval(self.update_color, 0.1)

    def redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Background
            Color(0.2, 0.2, 0.2)
            Ellipse(pos=self.pos, size=self.size)
            
            # Gauge arc
            Color(1, 1, 1)
            Line(circle=(self.center_x, self.center_y, self.width/2.5), 
                 width=15, 
                 cap='none')
            
            # Progress arc
            ratio = min(self.value / self.max_value, 1)
            Color(1 - ratio, ratio, 0)
            Line(circle=(self.center_x, self.center_y, self.width/2.5), 
                 width=30, 
                 cap='none',
                 angle=150,
                 span_angle=240*ratio)

    def update_color(self, dt):
        ratio = min(self.value / self.max_value, 1)
        self.color = (1 - ratio, ratio, 0, 1)

class MainScreen(Screen):
    pm25 = StringProperty("0.0")
    pm10 = StringProperty("0.0")

class HistoryScreen(Screen):
    def on_enter(self):
        self.update_history()

    def update_history(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM readings ORDER BY timestamp DESC LIMIT 20")
            rows = c.fetchall()
            
            self.ids.history_grid.clear_widgets()
            for row in rows:
                timestamp, pm25, pm10 = row
                entry = f"[{timestamp}] PM2.5: {pm25}, PM10: {pm10}"
                self.ids.history_grid.add_widget(Label(text=entry, size_hint_y=None, height='40dp'))
        except Exception as e:
            self.ids.history_grid.add_widget(Label(text=f"Error loading history: {str(e)}"))
        finally:
            conn.close()

class SettingsScreen(Screen):
    pass

class OnboardingPopup(Popup):
    pass

class GaugePopup(Popup):
    pass

class PuffApp(App):
    use_kivy_settings = False
    db_conn = None
    ai_client = None
    serial_port = None
    sensor_connected = False

    def build(self):
        self.setup_database()
        self.setup_window()
        self.setup_sensors()
        self.check_onboarding()
        return self.setup_ui()

    def setup_window(self):
        Window.size = (800, 480)
        Window.clearcolor = (0.15, 0.15, 0.15, 1)
        Window.bind(on_keyboard=self.handle_key)

    def setup_database(self):
        try:
            self.db_conn = sqlite3.connect(DB_NAME)
            c = self.db_conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS readings (
                    timestamp TEXT PRIMARY KEY,
                    pm25 REAL,
                    pm10 REAL
                )
            ''')
            self.db_conn.commit()
        except Exception as e:
            self.show_error(f"Database error: {str(e)}")

    def setup_sensors(self):
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "USB-SERIAL" in port.description:
                try:
                    self.serial_port = serial.Serial(port.device, BAUD_RATE, timeout=SERIAL_TIMEOUT)
                    self.sensor_connected = True
                    Clock.schedule_interval(self.read_sensor, 1)
                    return
                except Exception as e:
                    self.show_error(f"Sensor error: {str(e)}")
                    return
        self.show_error("SDS011 sensor not found")

    def setup_ui(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

    def check_onboarding(self):
        if not os.path.exists("setup_complete"):
            OnboardingPopup().open()
            with open("setup_complete", "w") as f:
                f.write("1")

    def read_sensor(self, dt):
        if not self.sensor_connected:
            return

        try:
            self.serial_port.write(b"\xaa\xb4\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x02\x03\x01\xab")
            data = self.serial_port.read(10)
            if len(data) == 10:
                pm25 = round((data[2] + data[3]*256)/10, 1)
                pm10 = round((data[4] + data[5]*256)/10, 1)
                
                self.root.get_screen('main').pm25 = str(pm25)
                self.root.get_screen('main').pm10 = str(pm10)
                self.root.get_screen('main').ids.gauge.value = pm25
                
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO readings VALUES (?, ?, ?)", 
                         (datetime.now().isoformat(), pm25, pm10))
                conn.commit()
                conn.close()
        except Exception as e:
            self.show_error(f"Sensor read error: {str(e)}")

    def toggle_theme(self):
        current = Window.clearcolor
        if current == [0.15, 0.15, 0.15, 1]:
            Window.clearcolor = (0.95, 0.95, 0.95, 1)
        else:
            Window.clearcolor = (0.15, 0.15, 0.15, 1)

    def show_error(self, message):
        popup = Popup(title="Error", content=Label(text=message), size_hint=(0.8, 0.3))
        popup.open()

    def generate_report(self):
        popup = GaugePopup()
        popup.ids.report_text.text = f"Current PM2.5: {self.root.get_screen('main').pm25}\\nPM10: {self.root.get_screen('main').pm10}"
        
        # AI integration (optional)
        api_key = self.root.get_screen('settings').ids.api_key.text
        if api_key:
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are Puff, a construction site air quality assistant"},
                        {"role": "user", "content": f"Analyze PM2.5: {self.root.get_screen('main').pm25} and PM10: {self.root.get_screen('main').pm10} for construction site safety"}
                    ]
                )
                popup.ids.report_text.text += f"\\n\\nAI Analysis:\\n{response.choices[0].message.content}"
            except Exception as e:
                popup.ids.report_text.text += f"\\n\\nAI Error: {str(e)}"
        
        popup.open()

    def handle_key(self, window, key, *args):
        if key == 27:  # ESC
            return True  # Disable escape

if __name__ == '__main__':
    PuffApp().run()
