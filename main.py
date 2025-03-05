import kivy
kivy.require('2.2.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from database import Database
from sensor import SDS011
from ai_assistant import PuffAI
from ui_components import Gauge, HistoryScreen
from onboarding import OnboardingScreen
from settings import SettingsScreen

import threading
import time

class RootScreenManager(ScreenManager):
    menu_visible = False
    sidebar = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sidebar = BoxLayout(orientation='vertical', size_hint_x=0.3)
        self._menu_anim = None

    def toggle_menu(self):
        if self.menu_visible:
            self.remove_widget(self.sidebar)
        else:
            self.add_widget(self.sidebar)
        self.menu_visible = not self.menu_visible

    def switch_to(self, screen_name):
        self.current = screen_name
        self.toggle_menu()

class AirQualityApp(App):
    db = ObjectProperty(Database())
    sensor = ObjectProperty(SDS011())
    ai = ObjectProperty(PuffAI())
    theme = 'light'

    def build(self):
        self.title = 'Air Quality Monitor'
        self.icon = 'assets/sprites/idle.png'
        self.root = RootScreenManager()
        
        # Start sensor reading thread
        self.sensor_thread = threading.Thread(target=self.read_sensor)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()
        
        # Initialize screens
        self.root.add_widget(OnboardingScreen(name='onboarding'))
        self.root.add_widget(HistoryScreen(name='history'))
        self.root.add_widget(SettingsScreen(name='settings'))
        
        # Check if first run
        if not self.config.get('General', 'first_run'):
            self.root.current = 'onboarding'
        else:
            self.root.current = 'main'
            
        return self.root

    def read_sensor(self):
        while True:
            pm25, pm10 = self.sensor.read_data()
            if pm25 and pm10:
                self.db.insert_reading(pm25, pm10)
                Clock.schedule_once(lambda dt: self.update_ui(pm25), 0)

    def update_ui(self, pm25):
        main_screen = self.root.get_screen('main')
        main_screen.ids.gauge.value = pm25
        self.ai.current_sprite.source = self.ai.sprites['idle']

    def on_stop(self):
        self.db.close()

    def save_settings(self):
        settings_screen = self.root.get_screen('settings')
        self.ai.set_api_key(settings_screen.ids.api_key.text)
        # Save sprite paths from settings_screen.ids.sprite_chooser.selection

    def toggle_theme(self):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        # Implement theme switching logic

if __name__ == '__main__':
    AirQualityApp().run()
  
