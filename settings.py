from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.label import Label

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Settings', font_size=30, size_hint_y=0.1))
        
        self.api_key_input = TextInput(
            hint_text='Enter OpenAI API Key',
            multiline=False,
            size_hint_y=0.1
        )
        layout.add_widget(self.api_key_input)
        
        self.sprite_chooser = FileChooserIconView(
            filters=['*.png'],
            size_hint_y=0.5
        )
        layout.add_widget(self.sprite_chooser)
        
        button_layout = BoxLayout(size_hint_y=0.2)
        save_btn = Button(text='Save Settings')
        save_btn.bind(on_press=self.save_settings)
        toggle_theme_btn = Button(text='Toggle Theme')
        toggle_theme_btn.bind(on_press=self.toggle_theme)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(toggle_theme_btn)
        layout.add_widget(button_layout)
        
        back_btn = Button(text='Back to Main', size_hint_y=0.1)
        back_btn.bind(on_press=self.go_to_main)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
    def save_settings(self, instance):
        app = App.get_running_app()
        app.ai.set_api_key(self.api_key_input.text)
        
    def toggle_theme(self, instance):
        app = App.get_running_app()
        app.theme = 'dark' if app.theme == 'light' else 'light'
        
    def go_to_main(self, instance):
        self.manager.current = 'main'
