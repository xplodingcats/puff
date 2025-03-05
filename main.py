import kivy
kivy.require('2.2.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.image import Image

from database import Database
from sensor import SDS011
from ai_assistant import PuffAI
from ui_components import Gauge
from onboarding import OnboardingScreen
from settings import SettingsScreen
import threading

class RootScreenManager(ScreenManager):
    menu_visible = False
    
    def toggle_menu(self):
        self.menu_visible = not self.menu_visible

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
        threading.Thread(target=self.read_sensor, daemon=True).start()
        
        # Initialize screens
        self.root.add_widget(OnboardingScreen(name='onboarding'))
        self.root.add_widget(self.create_main_screen())
        self.root.add_widget(SettingsScreen(name='settings'))
        
        return self.root

    def create_main_screen(self):
        from kivy.uix.screenmanager import Screen
        from kivy.uix.floatlayout import FloatLayout

        class MainScreen(Screen):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                layout = FloatLayout()
                
                # Gauge Widget
                self.gauge = Gauge(size_hint=(0.8, 0.8),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.6})
                layout.add_widget(self.gauge)
                
                # AI Sprite
                self.ai_sprite = Image(source='assets/sprites/idle.png',
                                      size_hint=(0.3, 0.3),
                                      pos_hint={'right': 0.95, 'y': 0.05})
                layout.add_widget(self.ai_sprite)
                
                # Menu Button
                menu_btn = Button(text='≡', size_hint=(0.1, 0.1),
                                pos_hint={'x': 0.02, 'top': 0.98})
                menu_btn.bind(on_press=self.root.toggle_menu)
                layout.add_widget(menu_btn)
                
                self.add_widget(layout)
                
            def update_gauge(self, pm25):
                self.gauge.value = pm25

        return MainScreen(name='main')

    def read_sensor(self):
        while True:
            pm25, pm10 = self.sensor.read_data()
            if pm25 is not None:
                self.db.insert_reading(pm25, pm10)
                Clock.schedule_once(lambda dt: self.update_ui(pm25), 0)

    def update_ui(self, pm25):
        main_screen = self.root.get_screen('main')
        main_screen.update_gauge(pm25)
        self.ai.current_sprite.source = self.ai.sprites['idle']

    def on_stop(self):
        self.db.close()

    def save_settings(self):
        settings_screen = self.root.get_screen('settings')
        self.ai.set_api_key(settings_screen.api_key_input.text)

    def toggle_theme(self):
        self.theme = 'dark' if self.theme == 'light' else 'light'

if __name__ == '__main__':
    AirQualityApp().run()
