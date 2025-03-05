from kivy.uix.screenmanager import Screen
from kivy.uix.carousel import Carousel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image

class OnboardingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        carousel = Carousel(direction='right')
        
        # Slide 1: Welcome
        slide1 = BoxLayout(orientation='vertical')
        slide1.add_widget(Image(source='assets/sprites/idle.png'))
        slide1.add_widget(Label(text='Welcome to Air Quality Monitor!', font_size=30))
        slide1.add_widget(Label(text='Swipe to learn how to use', font_size=20))
        
        # Slide 2: Main Screen
        slide2 = BoxLayout(orientation='vertical')
        slide2.add_widget(Image(source='assets/gauge_preview.png'))
        slide2.add_widget(Label(text='Main Screen shows real-time readings', font_size=25))
        
        # Slide 3: History
        slide3 = BoxLayout(orientation='vertical')
        slide3.add_widget(Image(source='assets/history_preview.png'))
        slide3.add_widget(Label(text='View historical data trends', font_size=25))
        
        # Slide 4: Settings
        slide4 = BoxLayout(orientation='vertical')
        slide4.add_widget(Image(source='assets/settings_preview.png'))
        slide4.add_widget(Label(text='Configure AI and appearance', font_size=25))
        
        carousel.add_widget(slide1)
        carousel.add_widget(slide2)
        carousel.add_widget(slide3)
        carousel.add_widget(slide4)
        
        done_btn = Button(text='Done', size_hint=(1, 0.2))
        done_btn.bind(on_press=self.switch_to_main)
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(carousel)
        layout.add_widget(done_btn)
        self.add_widget(layout)
        
    def switch_to_main(self, instance):
        self.manager.current = 'main'
